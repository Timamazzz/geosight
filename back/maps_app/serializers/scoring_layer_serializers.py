from rest_framework import serializers

from maps_app.models import CreateScoringMapLayerTask


class ScoringLayerSerializer(serializers.ModelSerializer):
    class Meta:
        model = CreateScoringMapLayerTask
        fields = '__all__'


class ScoringLayerListSerializer(serializers.ModelSerializer):
    maps = serializers.SerializerMethodField(label='Карта')
    layer = serializers.SerializerMethodField(label='Название')

    class Meta:
        model = CreateScoringMapLayerTask
        fields = ('id', 'layer', 'maps', 'status', 'created_at', 'end_time')

    def get_maps(self, obj):
        if obj.layer:
            maps = obj.layer.maps.all()
            return [map.name for map in maps]
        else:
            return None

    def get_layer(self,obj):
        return obj.layer.name if obj.layer else None

