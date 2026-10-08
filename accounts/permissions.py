from rest_framework.permissions import BasePermission

from accounts.models import User


class IsCandidate(BasePermission):
    message = 'Only candidates can access this endpoint.'

    def has_permission(self, request, view):
        return bool(
            request.user and request.user.is_authenticated and request.user.role == User.ROLE_CANDIDATE
        )


class IsRecruiter(BasePermission):
    message = 'Only recruiters can access this endpoint.'

    def has_permission(self, request, view):
        return bool(
            request.user and request.user.is_authenticated and request.user.role == User.ROLE_RECRUITER
        )


class IsApplicationOwner(BasePermission):
    message = 'You can only access your own applications.'

    def has_object_permission(self, request, view, obj):
        return obj.candidate == request.user


class IsRecruiterForApplication(BasePermission):
    message = 'You do not have access to this application.'

    def has_object_permission(self, request, view, obj):
        return obj.job.assigned_recruiter == request.user


class CanAccessApplication(BasePermission):
    message = 'You do not have permission to access this application.'

    def has_object_permission(self, request, view, obj):
        if request.user.role == User.ROLE_CANDIDATE:
            return obj.candidate == request.user
        if request.user.role == User.ROLE_RECRUITER:
            return obj.job.assigned_recruiter == request.user
        return False
