from drf_writable_nested import WritableNestedModelSerializer
from rest_framework import serializers

from maps_app.models import Map
from maps_app.serializers.map_layers_serializers import MapLayerShowSerializer
from maps_app.serializers.map_style_seralizers import MapStyleSerializer
from users_app.serializers.user_serializers import UserCardSerializer


class MapSerializer(serializers.ModelSerializer):
    class Meta:
        model = Map
        fields = '__all__'


class MapListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Map
        fields = ('id', 'name', 'updated_at', 'description')


class MapCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Map
        fields = ('name', 'description', 'style', 'company')
        extra_kwargs = {
            'company': {'required': False, 'allow_null': True}
        }


class MapUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Map
        fields = ('name', 'description')


class MapShareSerializer(WritableNestedModelSerializer):
    users = UserCardSerializer(many=True, allow_null=True)

    class Meta:
        model = Map
        fields = ('id', 'users')


class MapShowSerializer(WritableNestedModelSerializer):
    layers = MapLayerShowSerializer(many=True)
    style = MapStyleSerializer()

    class Meta:
        model = Map
        fields = ('id', 'name', 'description', 'style', 'layers')


class MapAllowedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Map
        fields = ('id', 'name', 'description', 'updated_at')


class MapStyleUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Map
        fields = ('id', 'style')
