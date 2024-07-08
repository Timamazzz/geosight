from django.urls import path, include
from rest_framework.routers import DefaultRouter

from maps_app.views import MapLayerViewSet, MapViewSet, MapStyleViewSet

router = DefaultRouter()
router.register(r'layers', MapLayerViewSet)
router.register(r'styles', MapStyleViewSet)
router.register(r'', MapViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
