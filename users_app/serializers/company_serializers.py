from rest_framework import serializers

from users_app.models import Company, User


class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = '__all__'


class CompanyRetrieveSerializer(serializers.ModelSerializer):
    users = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta:
        model = Company
        fields = ['id', 'name', 'users']


class CompanyUpdateSerializer(serializers.ModelSerializer):
    users = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta:
        model = Company
        fields = ['id', 'name', 'users']


class CompanyListSerializer(serializers.ModelSerializer):
    staff = serializers.SerializerMethodField()
    managers = serializers.SerializerMethodField()
    admins = serializers.SerializerMethodField()

    class Meta:
        model = Company
        fields = ['id', 'name', 'staff', 'managers', 'admins']

    def get_staff(self, obj):
        return User.objects.filter(company=obj, role='staff').count()

    def get_managers(self, obj):
        return User.objects.filter(company=obj, role='manager').count()

    def get_admins(self, obj):
        return User.objects.filter(company=obj, role='admin').count()


class CompanyCreateSerializer(serializers.ModelSerializer):
    users = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta:
        model = Company
        fields = ['name']
