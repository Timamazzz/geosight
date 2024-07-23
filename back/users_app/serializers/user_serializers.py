from rest_framework import serializers
from geosight.utils.fields import PhoneField
from users_app.models import User
from django.contrib.auth.hashers import make_password
from drf_writable_nested import WritableNestedModelSerializer
from django.core.files.storage import default_storage


ROLE_CHOICES = [
    ('staff', 'Сотрудник'),
    ('manager', 'Менеджер'),
    ('admin', 'Администратор'),
]


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'


class UserRetrieveSerializer(serializers.ModelSerializer):
    phone_number = PhoneField()

    class Meta:
        model = User
        fields = ['id', 'avatar', 'first_name', 'last_name', 'phone_number', 'email', 'role']


class UserUpdateSerializer(serializers.ModelSerializer):
    phone_number = PhoneField()

    class Meta:
        model = User
        fields = ['id', 'avatar', 'first_name', 'last_name', 'phone_number', 'email']


class UserListSerializer(serializers.ModelSerializer):
    phone_number = PhoneField()

    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'role', 'phone_number', 'email']


class UserCreateSerializer(serializers.ModelSerializer):
    phone_number = PhoneField()
    role = serializers.ChoiceField(choices=ROLE_CHOICES, label="Роль", required=True)

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'phone_number', 'password', 'email', 'role', 'company']
        extra_kwargs = {
            'password': {'write_only': True}
        }


class UserEditSerializer(serializers.ModelSerializer):
    phone_number = PhoneField()
    role = serializers.ChoiceField(choices=ROLE_CHOICES, label="Роль", required=True)

    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'phone_number', 'email', 'role']


class UserCardSerializer(WritableNestedModelSerializer):
    avatar = serializers.CharField()

    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'email', 'avatar']
