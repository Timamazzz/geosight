from drf_writable_nested import WritableNestedModelSerializer
from rest_framework import serializers

from users_app.models import Company, User
from users_app.serializers.user_serializers import UserCardSerializer


class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = '__all__'


class CompanyRetrieveSerializer(WritableNestedModelSerializer):
    users = UserCardSerializer(many=True, read_only=True)

    class Meta:
        model = Company
        fields = ['id', 'name', 'users']


class CompanyUpdateSerializer(WritableNestedModelSerializer):
    users = UserCardSerializer(many=True)

    class Meta:
        model = Company
        fields = ['id', 'name', 'users']
        extra_kwargs = {
            'name': {'label': 'Введите название'},
            'users': {'label': 'Выберите пользователей'},
        }


class CompanyListSerializer(serializers.ModelSerializer):
    staff = serializers.SerializerMethodField(label='Сотрудники')
    managers = serializers.SerializerMethodField(label='Менеджеры')
    admins = serializers.SerializerMethodField(label='Администраторыы')

    class Meta:
        model = Company
        fields = ['id', 'name', 'staff', 'managers', 'admins']

    def get_staff(self, obj):
        return User.objects.filter(company=obj, role='staff').count()

    def get_managers(self, obj):
        return User.objects.filter(company=obj, role='manager').count()

    def get_admins(self, obj):
        return User.objects.filter(company=obj, role='admin').count()


class CompanyCreateSerializer(WritableNestedModelSerializer):
    users = UserCardSerializer(many=True)

    class Meta:
        model = Company
        fields = ['name', 'users']
        extra_kwargs = {
            'name': {'label': 'Введите название'},
            'users': {'label': 'Выберите пользователей'},
        }
