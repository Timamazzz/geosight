from rest_framework import serializers

from maps_app.models import CreateScoringMapLayerTask


class ScoringLayerSerializer(serializers.ModelSerializer):
    class Meta:
        model = CreateScoringMapLayerTask
        fields = '__all__'


class ScoringLayerListSerializer(serializers.ModelSerializer):
    maps = serializers.SerializerMethodField(label='Карта')
    layer = serializers.CharField(source='layer.name', read_only=True, label='Название')

    class Meta:
        model = CreateScoringMapLayerTask
        fields = ('id', 'layer', 'maps', 'status', 'created_at', 'end_time')

    def get_maps(self, obj):
        if obj.layer:
            maps = obj.layer.maps.all()
            return [map.name for map in maps]
        else:
            return None
