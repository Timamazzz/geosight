from django.conf import settings
from django.contrib.auth.password_validation import validate_password
from post_office import mail
from rest_framework import serializers

from users_app.models import ActivationCode


class SendActivationCodeSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True, label='Почта')

    def send_activation_code(self, user):
        activation_code = ActivationCode.objects.create(user=user).code

        subject = 'Код подтверждения'
        message = f'Ваш код подтверждения: {activation_code}'
        html_message = f'Ваш код подтверждения: {activation_code}'

        mail.send(
            user.email,
            settings.DEFAULT_FROM_EMAIL,
            subject=subject,
            message=message,
            html_message=html_message,
            priority='now'
        )


class CheckActivationCodeSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True, label='Почта')
    code = serializers.CharField(max_length=4, required=True, label='Код подтверждения')


class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True, label='Почта')
    code = serializers.CharField(max_length=4, required=True, label='Код подтверждения')
    password = serializers.CharField(write_only=True, validators=[validate_password], required=True, label='Новый пароль')
    password_confirm = serializers.CharField(write_only=True, required=True, label='Введите новый пароль еще раз')

    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError("Passwords do not match.")
        return data
