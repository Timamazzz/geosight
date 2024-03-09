from rest_framework import permissions


class UserRolePermission(permissions.BasePermission):
    """
    Базовое разрешение для определенных ролей пользователей
    """

    allowed_roles = []

    def has_permission(self, request, view):
        return request.user and request.user.role in self.allowed_roles


class IsUser(UserRolePermission):
    """
    Разрешение для пользователя
    """
    allowed_roles = ['user', 'staff', 'manager', 'admin']


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
