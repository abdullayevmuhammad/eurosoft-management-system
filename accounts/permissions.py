# accounts/permissions.py
from rest_framework.permissions import BasePermission


class IsOwner(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.role == 'OWNER')


class IsOwnerOrPM(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.role in ['OWNER', 'PM'])


class IsDeveloper(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.role == 'DEV')


class IsNotViewer(BasePermission):

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.role != 'VIEWER')
