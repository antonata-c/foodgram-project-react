from rest_framework import permissions


class AdminOrAuthorOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        return (request.method in permissions.SAFE_METHODS
                or request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        return (request.method in permissions.SAFE_METHODS
                or (request.user.is_authenticated
                    and (obj.author == request.user
                         or request.user.is_superuser
                         or request.user.is_staff)))


class IsAuthenticatedOrReadOnlyObject(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.user.is_authenticated
