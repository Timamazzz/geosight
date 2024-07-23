from drf_writable_nested import WritableNestedModelSerializer
from rest_framework import serializers

from users_app.models import Company, User
from users_app.serializers.user_serializers import UserCardSerializer


class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = '__all__'


class CompanyRetrieveSerializer(WritableNestedModelSerializer):

    class Meta:
        model = Company
        fields = ['id', 'name']


class CompanyUpdateSerializer(WritableNestedModelSerializer):

    class Meta:
        model = Company
        fields = ['id', 'name',]
        extra_kwargs = {
            'name': {'label': 'Введите название'},
        }


class CompanyListSerializer(serializers.ModelSerializer):
    staff = serializers.SerializerMethodField(label='Сотрудники')
    managers = serializers.SerializerMethodField(label='Менеджеры')

    class Meta:
        model = Company
        fields = ['id', 'name', 'staff', 'managers', 'admins']

    def get_staff(self, obj):
        return User.objects.filter(company=obj, role='staff').count()

    def get_managers(self, obj):
        return User.objects.filter(company=obj, role='manager').count()


class CompanyCreateSerializer(WritableNestedModelSerializer):

    class Meta:
        model = Company
        fields = ['name']
        extra_kwargs = {
            'name': {'label': 'Введите название'},
        }
