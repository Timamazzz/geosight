from django.db.models import Min, Max, F, BigIntegerField, FloatField
from django.db.models.functions import Cast
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from geosight.utils.ModelViewSet import ModelViewSet
from maps_app.models import Map, MapLayer, MapStyle, CreateScoringMapLayerTask, Feature, MapLayerFilter, POIConfig
from maps_app.serializers.map_layers_serializers import (MapLayerSerializer, MapLayerListSerializer, \
                                                         MapLayerCreateSerializer, MapLayerUpdateSerializer,
                                                         MapLayerScoringCreateSerializer, MapLayerPropertiesSerializer, \
                                                         MapLayerUpdateLineStylesSerializer,
                                                         MapLayerUpdatePointStylesSerializer,
                                                         MapLayerUpdatePolygonStylesSerializer,
                                                         POISerializer)
from maps_app.serializers.map_serializers import MapSerializer, MapListSerializer, MapCreateSerializer, \
    MapUpdateSerializer, MapShareSerializer, MapShowSerializer
from maps_app.serializers.map_layer_filter_serializers import MapLayerFilterListLayerSerializer, \
    MapLayerFilterCreateSerializer, MapLayerFilterUpdateSerializer
from users_app.permissions import IsStaff, IsManager, IsSuperUser
from users_app.serializers.user_serializers import UserCardSerializer
from users_app.models import User

from .serializers.map_serializers import MapAllowedSerializer, MapStyleUpdateSerializer
from .serializers.map_style_seralizers import MapStyleSerializer
from .tasks import create_features, create_scoring_features
from users_app.utils import has_company_access
from post_office import mail
from django.conf import settings


# Create your views here.
class MapViewSet(ModelViewSet):
    queryset = Map.objects.all()
    serializer_class = MapSerializer
    serializer_list = {
        'list': MapListSerializer,
        'create': MapCreateSerializer,
        'update': MapUpdateSerializer,
        'share': MapShareSerializer,
        'show': MapShowSerializer,
        'map_style': MapStyleUpdateSerializer,
        'get_allowed_users': UserCardSerializer,
    }
    search_fields = ['name', 'description']

    def get_permissions(self):
        if self.action in ['show', 'map_style', 'allowed']:
            permission_classes = [IsStaff]
        elif self.action in ['create', 'update', 'list', 'destroy']:
            permission_classes = [IsManager]
        else:
            permission_classes = [IsSuperUser]

        return [permission() for permission in permission_classes]

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user

        if not user.is_admin:
            company = user.company

            if company:
                queryset = queryset.filter(company=company)
            else:
                return Response('У пользователя нет компании', status=status.HTTP_400_BAD_REQUEST)

        return queryset

    def perform_create(self, serializer):
        user = self.request.user
        if user.is_manager:
            serializer.save(company=user.company, creator=user)
        if user.is_admin:
            serializer.save(creator=user)

    @action(methods=['get'], detail=True)
    def show(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            user = request.user

            if has_company_access(user, instance.company) or user in instance.users.all():
                serializer = self.get_serializer(instance)
                return Response(serializer.data)
            else:
                return Response({"detail": "У вас нет доступа к этой карте."}, status=status.HTTP_403_FORBIDDEN)
        except self.model.DoesNotExist:
            return Response({"detail": "Карта не найдена."}, status=status.HTTP_404_NOT_FOUND)

    @action(methods=['get'], detail=False)
    def allowed(self, request):
        user = request.user
        if user.role == 'admin':
            allowed_maps = Map.objects.all()
        elif user.role == 'manager':
            allowed_maps = Map.objects.filter(company=user.company)
        else:
            allowed_maps = Map.objects.filter(users=user)
        serializer = MapAllowedSerializer(allowed_maps, many=True)
        return Response(serializer.data)

    @action(methods=['put'], detail=True)
    def map_style(self, request, pk=None):
        map_instance = self.get_object()
        if has_company_access(request.user, map_instance.company) or request.user in map_instance.users.all():
            serializer = MapStyleUpdateSerializer(map_instance, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"detail": "У вас нет доступа к этой карте."}, status=status.HTTP_403_FORBIDDEN)

    @action(methods=['get'], detail=True, url_path='get-allowed-users')
    def get_allowed_users(self, request, pk=None):
        map_instance = self.get_object()
        users = map_instance.users.all()
        users = users.exclude(id=request.user.id)

        page = self.paginate_queryset(users)
        if page is not None:
            serializer = UserCardSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = UserCardSerializer(users, many=True)
        return Response(serializer.data)

    @action(methods=['post'], detail=True, url_path='remove-allowed-users')
    def remove_allowed_users(self, request, pk=None):
        map_instance = self.get_object()
        user_id = request.query_params.get('user')

        if not has_company_access(request.user, map_instance.company):
            return Response({"detail": "У вас нет доступа к этой карте."}, status=status.HTTP_403_FORBIDDEN)

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({'detail': 'Пользователь не найден.'}, status=status.HTTP_404_NOT_FOUND)

        if user in map_instance.users.all():
            map_instance.users.remove(user)

            users = map_instance.users.all().exclude(id=request.user.id)

            page = self.paginate_queryset(users)
            if page is not None:
                serializer = UserCardSerializer(page, many=True)
                return self.get_paginated_response(serializer.data)

            serializer = UserCardSerializer(users, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response({'detail': 'Пользователь не прикреплен к карте.'}, status=status.HTTP_400_BAD_REQUEST)

    @action(methods=['post'], detail=True, url_path='sign-allowed-users')
    def sign_allowed_users(self, request, pk=None):
        map_instance = self.get_object()
        user_id = request.query_params.get('user')
        map_url = request.query_params.get('map_url')
        try:
            new_allowed_user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({'detail': 'Пользователь не найден.'}, status=status.HTTP_404_NOT_FOUND)

        if not has_company_access(request.user, map_instance.company):
            return Response({"detail": "У вас нет доступа к этой карте."}, status=status.HTTP_403_FORBIDDEN)

        map_instance.users.add(new_allowed_user)

        subject = 'Доступ к карте'
        message = f'Вы получили доступ к карте. Вы можете просмотреть карту по следующей ссылке: {map_url}'
        html_message = f'<p>Вы получили доступ к карте.</p><p>Вы можете просмотреть карту по следующей ссылке: <a href="{map_url}">{map_url}</a></p>'

        mail.send(
            new_allowed_user.email,
            settings.DEFAULT_FROM_EMAIL,
            subject=subject,
            message=message,
            html_message=html_message,
            priority='now'
        )
        users = map_instance.users.all().exclude(id=request.user.id)

        page = self.paginate_queryset(users)
        if page is not None:
            serializer = UserCardSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = UserCardSerializer(users, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if request.user.is_manager:
            if not has_company_access(request.user, instance.company):
                return Response({"detail": "У вас нет доступа к этой карте."}, status=status.HTTP_403_FORBIDDEN)

        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)


class MapLayerViewSet(ModelViewSet):
    queryset = MapLayer.objects.all()
    serializer_class = MapLayerSerializer
    serializer_list = {
        'list': MapLayerListSerializer,
        'create': MapLayerCreateSerializer,
        'update': MapLayerUpdateSerializer,
        'scoring': MapLayerScoringCreateSerializer,
        'properties': MapLayerPropertiesSerializer,
        'line': MapLayerUpdateLineStylesSerializer,
        'point': MapLayerUpdatePointStylesSerializer,
        'polygon': MapLayerUpdatePolygonStylesSerializer,
        'filters': MapLayerFilterListLayerSerializer,
        'filter-create': MapLayerFilterCreateSerializer,
        'filter-update': MapLayerFilterUpdateSerializer,
        'poi': POISerializer
    }
    search_fields = ['name', 'description']

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user

        if not user.is_admin:
            company = user.company

            if company:
                queryset = queryset.filter(maps__company=company).distinct()
            else:
                return Response('У пользователя нет компании', status=status.HTTP_400_BAD_REQUEST)

        return queryset

    def get_permissions(self):
        if self.action in ['line', 'point', 'polygon', 'list_filters', 'create_filter', 'delete_filter', 'edit_filter']:
            permission_classes = [IsStaff]
        elif self.action in ['create', 'update']:
            permission_classes = [IsManager]
        else:
            permission_classes = [IsSuperUser]

        return [permission() for permission in permission_classes]

    def perform_create(self, serializer):
        files = self.request.FILES.getlist('file')
        file = files[0] if files else None
        instance = serializer.save(creator=self.request.user)

        if file:
            if file.name.endswith(('.geojson', '.csv')):
                create_features.delay(instance.id, file.name, file.read())
            else:
                instance.error = 'Unsupported file type'
                instance.save()

    @action(detail=False, methods=['post'])
    def scoring(self, request):

        in_progress_tasks = CreateScoringMapLayerTask.objects.filter(
            status='in_progress').count()

        if in_progress_tasks >= 3:
            return Response({"detail": "Превышено максимальное количество выполняемых задач. Попробуйте позже."},
                            status=status.HTTP_429_TOO_MANY_REQUESTS)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        layer = serializer.save(creator=request.user)

        poi_data = request.data.get('poi', [])
        polygon_radius = request.data.get('polygon_radius', 0)

        print('poi_data scoring view:', poi_data)
        print('polygon_radius scoring view:', polygon_radius)
        task = create_scoring_features.delay(layer.id, poi_data, polygon_radius)

        CreateScoringMapLayerTask.objects.create(task_id=task.id, layer=layer,
                                                 status='in_progress')

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(methods=['get'], detail=False)
    def poi(self, request):
        poi_queryset = POIConfig.objects.all()
        serializer = POISerializer(poi_queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'])
    def properties(self, request, pk=None):
        map_layer = self.get_object()
        features = Feature.objects.filter(map_layer=map_layer)

        if not features.exists():
            return Response([], status=status.HTTP_200_OK)

        sample_properties = features.first().properties
        unique_keys = []

        type_mapping = {
            str: 'string',
            int: 'integer',
            float: 'float',
            bool: 'boolean',
            list: 'array',
            dict: 'object',
            type(None): 'null'
        }

        requested_types = request.query_params.getlist('types')
        allowed_types = set(type_mapping.values())

        if requested_types:
            requested_types = set(requested_types).intersection(allowed_types)
        else:
            requested_types = allowed_types

        for key, value in sample_properties.items():
            value_type = type_mapping.get(type(value), 'unknown')
            if value_type in requested_types:
                unique_keys.append({"name": key, "type": value_type})

        serializer = MapLayerPropertiesSerializer(unique_keys, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'], url_path='property-values-integer')
    def property_values_int(self, request, pk=None):
        return self._get_property_values(request, pk, int)

    @action(detail=True, methods=['get'], url_path='property-values-float')
    def property_values_float(self, request, pk=None):
        return self._get_property_values(request, pk, float)

    @action(detail=True, methods=['get'], url_path='property-values-string')
    def property_values_string(self, request, pk=None):
        return self._get_property_values(request, pk, str)

    def _get_property_values(self, request, pk, expected_type):
        map_layer = self.get_object()
        property_name = request.query_params.get('property_name')

        if not property_name:
            return Response({"detail": "Параметр 'property_name' обязателен."}, status=status.HTTP_400_BAD_REQUEST)

        features = Feature.objects.filter(map_layer=map_layer).values_list(f'properties__{property_name}',
                                                                           flat=True).distinct()

        if not features.exists():
            return Response({"detail": f"No features found with the property '{property_name}'."},
                            status=status.HTTP_404_NOT_FOUND)

        sample_value = features.first()

        if isinstance(sample_value, expected_type):
            if expected_type in [int, float]:
                return self._get_numeric_property_values(features, sample_value, property_name)
            elif expected_type == str:
                return self._get_string_property_values(features, request)
        else:
            return Response({"detail": f"Property '{property_name}' is not of type {expected_type.__name__}."},
                            status=status.HTTP_400_BAD_REQUEST)

    def _get_numeric_property_values(self, features, sample_value, property_name):
        features_casted = None
        if isinstance(sample_value, int):
            features_casted = features.annotate(
                property_value_casted=Cast(F(f'properties__{property_name}'), output_field=BigIntegerField())
            )
        elif isinstance(sample_value, float):
            features_casted = features.annotate(
                property_value_casted=Cast(F(f'properties__{property_name}'), output_field=FloatField())
            )
        if features_casted:
            min_value = features_casted.aggregate(min_value=Min('property_value_casted'))['min_value']
            max_value = features_casted.aggregate(max_value=Max('property_value_casted'))['max_value']
            return Response({
                'min_value': min_value,
                'max_value': max_value,
            }, status=status.HTTP_200_OK)
        else:
            return Response({"error": "Ошибка при аннотации данных."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _get_string_property_values(self, features, request):
        limit = int(request.query_params.get('limit', 10))
        offset = int(request.query_params.get('offset', 0))
        search_query = request.query_params.get('search', None)

        unique_values = list(set(features))
        if search_query:
            unique_values = [value for value in unique_values if value and search_query.lower() in value.lower()]

        total_count = len(unique_values)
        paginated_values = unique_values[offset:offset + limit]

        return Response({
            'results': paginated_values,
            'count': total_count,
            'limit': limit,
            'offset': offset,
        }, status=status.HTTP_200_OK)

    # Чтобы нормально настроить права для методов редактирования стилей, нужно перенести их в viewset map, так как мы не знаем из какой карты мы вызываем эти методы
    @action(detail=True, methods=['put'])
    def line(self, request, pk=None):
        map_layer = self.get_object()
        serializer = self.get_serializer(map_layer, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['put'])
    def point(self, request, pk=None):
        map_layer = self.get_object()
        serializer = self.get_serializer(map_layer, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['put'])
    def polygon(self, request, pk=None):
        map_layer = self.get_object()
        serializer = self.get_serializer(map_layer, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    # Фильтрация привязано к слою, но так же не учитывает карты, а значит из какой бы карты не был бы создан фильтр для слоя, он появиться и будет применен для каждой карты, нужно добавить ссылку на карту! Так же стоит перенести во ViwSet Карт!
    @action(detail=True, methods=['get'], url_path='filters')
    def list_filters(self, request, pk=None):
        map_layer = self.get_object()
        filters = MapLayerFilterListLayerSerializer.objects.filter(map_layer=map_layer)
        serializer = MapLayerFilterListLayerSerializer(filters, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='filters')
    def create_filter(self, request, pk=None):
        map_layer = self.get_object()
        serializer = MapLayerFilterCreateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(map_layer=map_layer)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['delete'], url_path='filters/(?P<filter_id>[^/.]+)')
    def delete_filter(self, request, pk=None, filter_id=None):
        map_layer = self.get_object()
        try:
            filter_instance = MapLayerFilter.objects.get(map_layer=map_layer, id=filter_id)
            filter_instance.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except MapLayerFilter.DoesNotExist:
            return Response({"detail": "Фильтр не найден."}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['put'], url_path='filters/(?P<filter_id>[^/.]+)')
    def edit_filter(self, request, pk=None, filter_id=None):
        map_layer = self.get_object()
        try:
            filter_instance = MapLayerFilter.objects.get(map_layer=map_layer, id=filter_id)
            serializer = MapLayerFilterUpdateSerializer(filter_instance, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except MapLayerFilter.DoesNotExist:
            return Response({"detail": "Фильтр не найден."}, status=status.HTTP_404_NOT_FOUND)


class MapStyleViewSet(ModelViewSet):
    queryset = MapStyle.objects.all()
    serializer_class = MapStyleSerializer
    serializer_list = {
        'list': MapStyleSerializer,
    }
