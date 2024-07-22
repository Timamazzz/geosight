from rest_framework import serializers

from maps_app.models import CreateScoringMapLayerTask


class ScoringLayerSerializer(serializers.ModelSerializer):
    class Meta:
        model = CreateScoringMapLayerTask
        fields = '__all__'


class ScoringLayerListSerializer(serializers.ModelSerializer):
    maps = serializers.SerializerMethodField()

    class Meta:
        model = CreateScoringMapLayerTask
        fields = ('id', 'task_id', 'layer', 'maps', 'status', 'created_at', 'end_time')

    def get_maps(self, obj):
        maps = obj.layer.maps.all()
        return [map.name for map in maps]
