from rest_framework import permissions
from rest_framework.permissions import BasePermission


class UserRolePermission(permissions.BasePermission):
    """
    Базовое разрешение для определенных ролей пользователей
    """

    allowed_roles = []

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role in self.allowed_roles)


class IsStaff(UserRolePermission):
    """
    Разрешение для сотрудника
    """
    allowed_roles = ['staff', 'manager', 'admin']


class IsManager(UserRolePermission):
    """
    Разрешение для менеджера
    """
    allowed_roles = ['manager', 'admin']


class IsAdmin(UserRolePermission):
    """
    Разрешение для админа
    """
    allowed_roles = ['admin']


class IsSuperUser(BasePermission):
    """
    Allows access only to admin users.
    """

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_superuser)
