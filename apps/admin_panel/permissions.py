
from rest_framework.permissions import BasePermission
from apps.accounts.models import User


class IsSupportAdmin(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role in [
                User.Role.SUPPORT,
                User.Role.SUPER_ADMIN,
            ]
        )


class IsFinanceAdmin(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role in [
                User.Role.FINANCE,
                User.Role.SUPER_ADMIN,
            ]
        )


class IsSuperAdmin(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role == User.Role.SUPER_ADMIN
        )