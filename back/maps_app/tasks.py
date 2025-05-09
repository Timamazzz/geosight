from celery import shared_task
import json
import csv
from maps_app.models import MapLayer, CreateScoringMapLayerTask
from maps_app.utils import process_geojson_features, process_csv_features, process_scoring_features, \
    send_layer_activity_update
from django.utils import timezone


@shared_task(name="create_features")
def create_features(map_layer_id, file_name, file_contents):
    print('Starting create_features task')
    instance = MapLayer.objects.get(id=map_layer_id)
    try:
        print(f'Processing layer: {instance.name}')

        if file_name.endswith('.geojson'):
            geojson = json.loads(file_contents)
            process_geojson_features(geojson, instance)

        elif file_name.endswith('.csv'):
            decoded_file = file_contents.decode('utf-8').splitlines()
            reader = csv.DictReader(decoded_file)
            process_csv_features(reader, instance)

        else:
            instance.error = 'Unsupported file type'
            instance.save()
            print(f'Unsupported file type for layer: {instance.name}')
            return

        instance.is_active = True
        instance.save()
        print(f'Complete create features for layer: {instance.name}')

        send_layer_activity_update(instance)
    except Exception as e:
        print(f'Error processing layer {instance.name}: {e}')


@shared_task(name="create_scoring_features")
def create_scoring_features(map_layer_id, poi_data, polygon_radius):
    print('map_layer_id create_scoring_features:', map_layer_id)
    print('poi_data create_scoring_features:', poi_data)
    print('polygon_radius create_scoring_features:', polygon_radius)
    instance = MapLayer.objects.get(id=map_layer_id)
    print('create_scoring_features', instance)
    task = CreateScoringMapLayerTask.objects.get(layer=instance)
    try:
        print(f'Processing layer: {instance.name}')
        process_scoring_features(map_layer_id, task, poi_data, polygon_radius)
        instance.is_active = True
        instance.save()
        task.status = 'completed'
        task.end_time = timezone.now()
        task.save()
        print(f'Complete create features for layer: {instance.name}')

        send_layer_activity_update(instance)
    except Exception as e:
        task.status = 'failed'
        task.error_message = str(e)
        task.end_time = timezone.now()
        task.save()
        print(f'Error processing layer {instance.name}: {e}')
