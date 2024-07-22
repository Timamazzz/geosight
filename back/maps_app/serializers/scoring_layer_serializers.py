from rest_framework import serializers

from maps_app.models import CreateScoringMapLayerTask


class ScoringLayerSerializer(serializers.ModelSerializer):
    class Meta:
        model = CreateScoringMapLayerTask
        fields = '__all__'


class ScoringLayerListSerializer(serializers.ModelSerializer):
    maps = serializers.SerializerMethodField()
    companies = serializers.SerializerMethodField()

    class Meta:
        model = CreateScoringMapLayerTask
        fields = ('id', 'task_id', 'layer', 'maps', 'status', 'created_at', 'end_time', 'companies')

    def get_map(self, obj):
        maps = obj.layer.maps.all()
        return [map.name for map in maps]

    def get_companies(self, obj):
        request = self.context.get('request')
        companies = obj.layer.maps.filter(company=request.user.company).distinct()
        return [company.pk for company in companies]
