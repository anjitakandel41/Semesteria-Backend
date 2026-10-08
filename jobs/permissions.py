from rest_framework.permissions import BasePermission


class IsAuthenticatedJobUser(BasePermission):
    message = 'Authentication required.'

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)
