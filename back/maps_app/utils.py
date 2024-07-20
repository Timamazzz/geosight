import os
from django.db import transaction
from django.contrib.gis.geos import GEOSGeometry
import json
import h3
import geopandas as gpd
import numpy as np
from sqlalchemy import create_engine
from math import *
from geosight.settings import BASE_DIR
from maps_app.models import Feature
from pyproj import Transformer
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

MAX_SIZE_FEATURES = 5000


def process_geojson_features(geojson, instance):
    features_to_create = []
    for feature in geojson['features']:
        geom = GEOSGeometry(json.dumps(feature['geometry']))
        feature_type = feature['type']
        properties = feature.get('properties', {})
        features_to_create.append(
            Feature(
                map_layer=instance,
                geometry=geom,
                type=feature_type,
                properties=properties
            )
        )
        if len(features_to_create) >= MAX_SIZE_FEATURES:
            save_features(features_to_create)
            features_to_create = []

    if features_to_create:
        save_features(features_to_create)


def process_csv_features(reader, instance):
    features_to_create = []
    for row in reader:
        h3_index = row.pop('h3')
        geom = GEOSGeometry(json.dumps({
            "type": "Polygon",
            "coordinates": [h3.h3_to_geo_boundary(h3_index, geo_json=True)]
        }))
        features_to_create.append(
            Feature(
                map_layer=instance,
                geometry=geom,
                type='Feature',
                properties=row
            )
        )
        if len(features_to_create) >= MAX_SIZE_FEATURES:
            save_features(features_to_create)
            features_to_create = []

    if features_to_create:
        save_features(features_to_create)


def save_features(features_to_create):
    print(f'Saving {len(features_to_create)} features to database')
    with transaction.atomic():
        Feature.objects.bulk_create(features_to_create)


def setup_grid(path_to_grid):
    # Загружаем грид и создаём пространственный индекс
    grid = gpd.read_file(path_to_grid).to_crs('3857')
    grid.sindex
    grid['score'] = 0

    return grid


def calculate_scoring(engine, grid, poi_list, polygon_radius, task):
    max_poi_list = len(poi_list)
    processed_poi_count = 0
    for poi, params in poi_list.items():
        # Loading table data from db and creating spatial indexes
        data = gpd.read_postgis(f'SELECT * FROM {poi}', engine)
        data.sindex

        # Создаём в датафрейме сетки колонку для баллов по определенному параметры
        grid[poi] = 0

        # В переменной хранится макс. первичный балл по полигону в категории, в списке все первичные баллы по полигонам
        max_score_pp = 0
        scores_pp = {}

        print(poi)

        for index, poly in grid.iterrows():
            # Getting centroids
            centroid = poly.geometry.centroid
            centroid_buff = centroid.buffer(params['max-distance'] + polygon_radius)

            # Вытаскиваем все индексы, которые находятся в bbox и ищем совпадения в радиусе
            possible_matches_index = list(data.sindex.intersection(centroid_buff.bounds))
            matches = data.iloc[possible_matches_index]
            target_points = matches[matches.intersects(centroid_buff)]

            # В переменную записываем количество первичных баллов конкретного полигона конкретной категории
            poly_score = 0

            for _, point in target_points.iterrows():
                # Ищем расстояние от точки до центроиды
                dist_to_centroid = point.geom.distance(centroid)

                # Считаем балл за конкретную точку (меньше расстояние - больше балл) от 0 до 1
                p_rad = polygon_radius
                poly_score += np.interp(dist_to_centroid, [p_rad, params['max-distance'] + p_rad], [1, 0], left=1,
                                        right=0)

            # Добавляем полученный балл в список
            scores_pp[index] = poly_score

            # Обновляем макс. значение при необходимости
            if poly_score > max_score_pp:
                max_score_pp = poly_score

            # Для удобства вывода
            if index % 10000 == 0:
                print(f'{index}/{len(grid)}')

        # Пробегаем по списку с первичными баллами и считаем вторичный балл для каждого полигона
        for index, poly in grid.iterrows():
            # Считаем вторичный балл как логарифмическую интерполяцию от 0 до макс. по основанию 2
            secondary_score = np.interp(pow(scores_pp[index], 1 / 8), [0, pow(max_score_pp, 1 / 8)],
                                        [0, params['max-score']])

            grid.loc[index, poi] = secondary_score
            grid.loc[index, 'score'] += secondary_score

        processed_poi_count += 1
        task.calculate_scoring_progress = (processed_poi_count / max_poi_list) * 100
        task.save()

    task.calculate_scoring_progress = 100
    task.save()

    return grid


def balance_values(grid):
    # Находим макс. значение полигонов по каждому городу
    max_scores = {}
    for index, poly in grid.iterrows():
        if max_scores.get(poly['city_name']) is None or poly['score'] > max_scores[poly['city_name']]:
            max_scores[poly['city_name']] = poly['score']

    # Размазываем полученные значения от 0 до ста с разбивкой на города (в каждом городе будет 100)
    for index, poly in grid.iterrows():
        current_score = grid.loc[index, 'score']
        grid.loc[index, 'score'] = np.interp(current_score, [0, max_scores[poly['city_name']]], [0, 100])

    return grid


def process_scoring_features(layer_id, task, poi_data, polygon_radius):
    engine = create_engine(
        f"postgresql://{os.getenv('DB_USER_OSM')}:{os.getenv('DB_PASSWORD_OSM')}@osm_db:5432/osm-data"
    )
    grid = setup_grid(os.path.join(BASE_DIR, 'maps_app', 'scoring', 'grid.gpkg'))

    active_poi_data = [poi for poi in poi_data if poi.get('is_active', False)]
    poi_list = {
        poi.name: {
            'max-score': poi.max_score,
            'max-distance': poi.max_distance
        }
        for poi in active_poi_data
    }

    grid = calculate_scoring(engine, grid, poi_list, polygon_radius, task)

    # Обсчитываем вторичный скоринг с разбивкой по городам
    grid = balance_values(grid)

    total_polygons = len(grid)
    processed_polygons = 0
    features_to_create = []

    for index, poly in grid.iterrows():
        processed_polygons += 1

        # Convert geometry to WKT and then transform
        geom_3857 = GEOSGeometry(poly['geometry'].wkt, srid=3857)
        geom_4326 = geom_3857.transform(4326, clone=True)

        properties = {'score': poly['score']}

        features_to_create.append(
            Feature(
                map_layer_id=layer_id,
                geometry=geom_4326,
                type='Feature',
                properties=properties
            )
        )

        if len(features_to_create) >= MAX_SIZE_FEATURES:
            save_features(features_to_create)
            features_to_create = []

            # Вычисляем прогресс выполнения задачи
            task.polygon_import_progress = (processed_polygons / total_polygons) * 100
            task.save()

    if features_to_create:
        save_features(features_to_create)

    task.polygon_import_progress = 100
    task.save()


def send_layer_activity_update(instance):
    try:
        channel_layer = get_channel_layer()
        for map_instance in instance.maps.all():
            group_name = f'map_{map_instance.id}_updates'
            async_to_sync(channel_layer.group_send)(
                group_name,
                {
                    'type': 'send_update',
                    'message': {
                        'type': 'layer_features_created',
                        'layer_id': instance.id,
                        'is_active': instance.is_active,
                    }
                }
            )
        print(f'Sent layer activity update for layer: {instance.name}')
    except Exception as e:
        print(f'Error sending layer activity update for layer {instance.name}: {e}')
