from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Company, ActivationCode


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ['email', 'phone_number', 'is_staff', 'is_superuser', 'is_active', 'company']
    list_filter = ['is_staff', 'is_superuser', 'is_active', 'company']
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'avatar', 'phone_number')}),
        ('Company Info', {'fields': ('company',)}),
        ('Permissions', {'fields': ('is_active', 'role', 'is_staff', 'is_superuser')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'is_staff', 'is_superuser', 'company'),
        }),
    )
    search_fields = ['email', 'phone_number']
    ordering = ['email']
    filter_horizontal = ()


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']


@admin.register(ActivationCode)
class ActivationCodeAdmin(admin.ModelAdmin):
    list_display = ['user', 'code', 'created_at', 'is_expired']
