from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from geosight.utils.CustomJWTSerializer import CustomJWTSerializer
from users_app import views

router = DefaultRouter()

urlpatterns = [

    path('login/', TokenObtainPairView.as_view(serializer_class=CustomJWTSerializer), name='token_obtain_pair'),
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('reset-password/', views.reset_password, name='reset_password'),
    path('', include(router.urls)),
]
