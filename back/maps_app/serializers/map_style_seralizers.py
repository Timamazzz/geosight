from rest_framework import serializers

from maps_app.models import MapStyle


class MapStyleSerializer(serializers.ModelSerializer):
    class Meta:
        model = MapStyle
        fields = '__all__'
