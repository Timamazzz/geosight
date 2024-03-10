from rest_framework import serializers

from geosight.utils.fields import PhoneField
from users_app.models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'


class UserRetrieveSerializer(serializers.ModelSerializer):
    phone_number = PhoneField()

    class Meta:
        model = User
        fields = ['id', 'avatar', 'first_name', 'last_name', 'phone_number', 'email']


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

