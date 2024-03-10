from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from geosight.utils.CustomJWTSerializer import CustomJWTSerializer
from users_app.views import SendActivationCodeView, ResetPasswordView, CheckActivationCodeView, \
    UserViewSet, CompanyViewSet

router = DefaultRouter()
router.register(r'companies', CompanyViewSet)
router.register(r'', UserViewSet)

urlpatterns = [
    path('login/', TokenObtainPairView.as_view(serializer_class=CustomJWTSerializer), name='token-obtain-pair'),
    path('refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('send-activation-code/', SendActivationCodeView.as_view(), name='send-activation-code'),
    path('check-activation-code/', CheckActivationCodeView.as_view(), name='check-activation-code'),
    path('reset-password/', ResetPasswordView.as_view(), name='reset-password'),
    path('', include(router.urls)),
]
