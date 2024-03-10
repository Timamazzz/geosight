from rest_framework import generics
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated

from geosight import settings
from geosight.utils.ModelViewSet import ModelViewSet
from geosight.utils.OptionsMetadata import OptionsMetadata
from users_app.models import User, ActivationCode
from users_app.permissions import IsUser, IsSuperUser, IsManager
from users_app.serializers.reset_password_serializers import SendActivationCodeSerializer, \
    CheckActivationCodeSerializer, ResetPasswordSerializer
from users_app.serializers.user_serializers import UserSerializer, UserRetrieveSerializer, UserUpdateSerializer, \
    UserListSerializer, UserCreateSerializer
from post_office import mail


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
        'create': UserCreateSerializer
    }

    def get_permissions(self):
        if self.action in ['retrieve', 'update']:
            permission_classes = [IsUser]
        elif self.action == 'list':
            permission_classes = [IsManager]
        elif self.action == 'destroy':
            permission_classes = [IsSuperUser]
        elif self.action == 'create':
            permission_classes = [IsManager]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        if request.user.role == 'manager':
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

        if request.user.role == 'manager':
            serializer.validated_data['company'] = request.user.company
        elif request.user.role == 'admin':
            if not serializer.validated_data['company']:
                return Response({'error': 'Не выбрана компания'}, status=status.HTTP_400_BAD_REQUEST)

        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)

        if serializer.validated_data['is_send_email']:
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
