from drf_writable_nested import WritableNestedModelSerializer
from rest_framework import serializers
from maps_app.models import MapLayerFilter

class MapLayerFilterSerializer(serializers.ModelSerializer):
    class Meta:
        model = MapLayerFilter
        fields = '__all__'

class MapLayerFilterCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = MapLayerFilter
        exclude = ('id',)

class MapLayerFilterListLayerSerializer(serializers.ModelSerializer):
    class Meta:
        model = MapLayerFilter
        fields = '__all__'

class MapLayerFilterUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = MapLayerFilter
        fields = '__all__'