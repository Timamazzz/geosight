from drf_writable_nested import WritableNestedModelSerializer
from rest_framework import serializers

from maps_app.models import MapLayer, POIConfig, Map


class MapLayerSerializer(serializers.ModelSerializer):
    class Meta:
        model = MapLayer
        fields = '__all__'


class MapLayerListSerializer(serializers.ModelSerializer):
    features_count = serializers.SerializerMethodField(label='Количество полигонов')
    maps_count = serializers.SerializerMethodField(label='Используется  в')

    class Meta:
        model = MapLayer
        fields = ('id', 'name', 'updated_at', 'features_count', 'maps_count', 'description')

    @staticmethod
    def get_features_count(obj):
        return obj.features.count()

    @staticmethod
    def get_maps_count(obj):
        return obj.maps.count()


class MapLayerCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = MapLayer
        fields = ('name', 'description', 'maps')


class MapLayerUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = MapLayer
        fields = ('id', 'name', 'description', 'maps')


class MapLayerShowSerializer(WritableNestedModelSerializer):
    class Meta:
        model = MapLayer
        fields = ('id', 'name', 'description', 'serialize_styles', 'is_active')


class POISerializer(serializers.ModelSerializer):
    is_active = serializers.BooleanField(default=True, label="Активный")
    name = serializers.CharField(max_length=100, label="Название")
    max_score = serializers.IntegerField(label="Вес")
    max_distance = serializers.IntegerField(label="Дситаниця")

    class Meta:
        model = POIConfig
        fields = ('is_active', 'name', 'max_score', 'max_distance')


class MapLayerScoringCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length='256', required=True, label='Название')
    description = serializers.CharField(required=False, allow_blank=True, label='Описание')
    maps = serializers.PrimaryKeyRelatedField(queryset=Map.objects.all(), label='Карта')
    polygon_radius = serializers.IntegerField(min_value=0, required=True, label='Полигон радиус')
    poi = POISerializer(many=True)

    class Meta:
        fields = ('name', 'description', 'maps', 'poi')


class MapLayerPropertiesSerializer(serializers.Serializer):
    FIELD_TYPE_CHOICES = [
        ('string', 'String'),
        ('integer', 'Integer'),
        ('float', 'Float'),
        ('boolean', 'Boolean'),
        ('array', 'Array'),
        ('object', 'Object'),
        ('null', 'Null'),
    ]
    name = serializers.CharField(label="Имя поля")
    type = serializers.ChoiceField(choices=FIELD_TYPE_CHOICES, label="Тип поля")

    class Meta:
        fields = '__all__'


class MapLayerUpdateLineStylesSerializer(serializers.ModelSerializer):
    class Meta:
        model = MapLayer
        fields = (
            'id',
            'line_opacity',
            'line_size',
            'line_style',
            'line_solid_color',
            'line_value_field_name',
            'line_color_palette'
        )


class MapLayerUpdatePointStylesSerializer(serializers.ModelSerializer):
    class Meta:
        model = MapLayer
        fields = (
            'id',
            'point_radius',
            'point_opacity',
            'point_solid_color',
            'point_value_field_name',
            'point_color_palette'
        )


class MapLayerUpdatePolygonStylesSerializer(serializers.ModelSerializer):
    class Meta:
        model = MapLayer
        fields = (
            'id',
            'polygon_opacity',
            'polygon_label',
            'polygon_label_font',
            'polygon_label_font_style',
            'polygon_label_font_size',
            'polygon_label_font_color',
            'polygon_label_font_opacity',
            'polygon_border_style',
            'polygon_border_size',
            'polygon_border_color',
            'polygon_border_opacity',
            'polygon_solid_color',
            'polygon_value_field_name',
            'polygon_color_palette'
        )


class MapFromMapLayerCreateSerializer(serializers.ModelSerializer):
    value = serializers.IntegerField(source='id')
    display_name = serializers.CharField(source='name')

    class Meta:
        model = Map
        fields = ('value', 'display_name')
