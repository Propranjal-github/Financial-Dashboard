from rest_framework.permissions import BasePermission


class IsAdmin(BasePermission):
    """Allow access only to users with the admin role."""

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == 'admin'
        )


class IsAnalystOrAbove(BasePermission):
    """Allow access to analysts and admins."""

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role in ('analyst', 'admin')
        )
