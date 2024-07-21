from rest_framework import generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny

from geosight import settings
from geosight.utils.ModelViewSet import ModelViewSet
from geosight.utils.OptionsMetadata import OptionsMetadata
from users_app.models import User, ActivationCode, Company
from users_app.serializers.company_serializers import CompanyListSerializer, CompanyCreateSerializer, \
    CompanyRetrieveSerializer, CompanyUpdateSerializer, CompanySerializer
from users_app.serializers.reset_password_serializers import SendActivationCodeSerializer, \
    CheckActivationCodeSerializer, ResetPasswordSerializer
from users_app.serializers.user_serializers import UserSerializer, UserRetrieveSerializer, UserUpdateSerializer, \
    UserListSerializer, UserCreateSerializer, UserEditSerializer, UserCardSerializer
from post_office import mail

from users_app.permissions import IsStaff, IsSuperUser, IsManager, IsAdmin

from users_app.utils import has_company_access
from django.db.models import Q

from maps_app.models import Map


class BaseResetPasswordView(generics.CreateAPIView):
    permission_classes = [AllowAny]
    metadata_class = OptionsMetadata

    def get_user(self, email):
        try:
            return User.objects.get(email=email)
        except User.DoesNotExist:
            return None

    def get_activation_code(self, user, code):
        try:
            return ActivationCode.objects.get(user=user, code=code)
        except ActivationCode.DoesNotExist:
            return None

    def validate_activation_code(self, activation_code):
        if activation_code.is_expired:
            return Response({"error": "Срок действия кода активации истек"}, status=status.HTTP_400_BAD_REQUEST)
        return None


class SendActivationCodeView(BaseResetPasswordView):
    serializer_class = SendActivationCodeSerializer
    serializer_list = {'create': SendActivationCodeSerializer}

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data.get('email', None)
        user = self.get_user(email)

        if user is None:
            return Response({"error": "Пользователь с таким адресом электронной почты не найден"},
                            status=status.HTTP_404_NOT_FOUND)

        serializer.send_activation_code(user)

        return Response({"message": "Код активации успешно отправлен"}, status=status.HTTP_200_OK)


class CheckActivationCodeView(BaseResetPasswordView):
    serializer_class = CheckActivationCodeSerializer
    serializer_list = {'create': CheckActivationCodeSerializer}

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data.get('email', None)
        user = self.get_user(email)

        if user is None:
            return Response({"error": "Пользователь с таким адресом электронной почты не найден"},
                            status=status.HTTP_404_NOT_FOUND)

        code = serializer.validated_data.get('code', None)
        activation_code = self.get_activation_code(user, code)

        if activation_code is None:
            return Response({"error": "Недействительный код активации"}, status=status.HTTP_400_BAD_REQUEST)

        error_response = self.validate_activation_code(activation_code)
        if error_response:
            return error_response

        return Response({"message": "Код активации действителен"}, status=status.HTTP_200_OK)


class ResetPasswordView(BaseResetPasswordView):
    serializer_class = ResetPasswordSerializer
    serializer_list = {'create': ResetPasswordSerializer}

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data.get('email', None)
        user = self.get_user(email)

        if user is None:
            return Response({"error": "Пользователь с таким адресом электронной почты не найден"},
                            status=status.HTTP_404_NOT_FOUND)

        code = serializer.validated_data.get('code', None)
        activation_code = self.get_activation_code(user, code)

        if activation_code is None:
            return Response({"error": "Недействительный код активации"}, status=status.HTTP_400_BAD_REQUEST)

        error_response = self.validate_activation_code(activation_code)
        if error_response:
            return error_response

        password = serializer.validated_data.get('password', None)
        user.set_password(password)
        user.save()

        activation_code.delete()

        return Response({"message": "Пароль успешно сброшен"}, status=status.HTTP_200_OK)


class UserViewSet(ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    serializer_list = {
        'retrieve': UserRetrieveSerializer,
        'update': UserUpdateSerializer,
        'list': UserListSerializer,
        'create': UserCreateSerializer,
        'edit': UserEditSerializer,
        'cards': UserCardSerializer
    }

    def get_permissions(self):
        if self.action in ['retrieve', 'update', 'cards']:
            permission_classes = [IsStaff]
        elif self.action in ['list', 'create', 'edit']:
            permission_classes = [IsManager]
        else:
            permission_classes = [IsSuperUser]
        return [permission() for permission in permission_classes]

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        if request.user.is_manager:
            queryset = queryset.filter(company=request.user.company)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if request.user.is_manager:
            serializer.validated_data['company'] = request.user.company
        elif request.user.is_admin:
            if not serializer.validated_data['company']:
                return Response({'error': 'Не выбрана компания'}, status=status.HTTP_400_BAD_REQUEST)

        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)

        if request.data.get('is_send_email', None):
            subject = 'Данные для входа'
            message = f'Добро пожаловать! Ваш логин: {serializer.validated_data["email"]}, ваш пароль: {serializer.validated_data["password"]}'
            html_message = f'<p>Добро пожаловать!</p><p>Ваш логин: {serializer.validated_data["email"]}</p><p>Ваш пароль: {serializer.validated_data["password"]}</p>'

            mail.send(
                serializer.validated_data['email'],
                settings.DEFAULT_FROM_EMAIL,
                subject=subject,
                message=message,
                html_message=html_message,
                priority='now'
            )

        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @action(detail=True, methods=['put', 'patch'])
    def edit(self, request, pk=None):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        if request.user.role == 'manager':
            if instance.company != request.user.company:
                return Response({'error': 'Недостаточно прав доступа'}, status=status.HTTP_403_FORBIDDEN)

        self.perform_update(serializer)
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()

        if not (has_company_access(request.user, instance.company) or request.user == instance):
            return Response({'error': 'Недостаточно прав доступа'}, status=status.HTTP_403_FORBIDDEN)

        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()

        if not (has_company_access(request.user, instance.company) or request.user == instance):
            return Response({'error': 'Недостаточно прав доступа'}, status=status.HTTP_403_FORBIDDEN)

        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        self.perform_update(serializer)
        return Response(serializer.data)

    @action(methods=['get'], detail=False)
    def cards(self, request):
        search_query = request.query_params.get('search', '')
        map_id = request.query_params.get('map', '')
        user = request.user

        if user.role == 'admin':
            queryset = User.objects.all()
        else:
            queryset = User.objects.filter(company=user.company)

        queryset = queryset.exclude(id=user.id)

        if search_query:
            queryset = queryset.filter(
                Q(first_name__icontains=search_query) |
                Q(last_name__icontains=search_query) |
                Q(email__icontains=search_query)
            )

        if map_id:
            try:
                map_instance = Map.objects.get(id=map_id)
                queryset = queryset.exclude(id__in=map_instance.users.values_list('id', flat=True))
            except Map.DoesNotExist:
                return Response({'detail': 'Карта не найдена.'}, status=status.HTTP_404_NOT_FOUND)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = UserCardSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = UserCardSerializer(queryset, many=True)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if request.user.is_manager:
            if request.user.company != instance.company:
                return Response({"detail": "У вас нет доступа."}, status=status.HTTP_403_FORBIDDEN)

        self.perform_destroy(instance)
        return Response({"message": "Как же я устал"}, status=status.HTTP_200_OK)

class CompanyViewSet(ModelViewSet):
    queryset = Company.objects.all()
    serializer_class = CompanySerializer
    serializer_list = {
        'retrieve': CompanyRetrieveSerializer,
        'update': CompanyUpdateSerializer,
        'list': CompanyListSerializer,
        'create': CompanyCreateSerializer,
    }
    permission_classes = [IsAdmin]
