from django.contrib.auth import get_user_model
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from .permissions import IsAdmin
from .serializers import (
    UserManagementSerializer,
    UserProfileSerializer,
)

User = get_user_model()


# ---------------------------------------------------------------------------
# Auth views
# ---------------------------------------------------------------------------


class LogoutView(generics.GenericAPIView):
    """
    Logout by blacklisting the refresh token.
    Client should also discard the access token on its side.
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response(
                {'detail': 'Refresh token is required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except Exception:
            return Response(
                {'detail': 'Invalid or already blacklisted token.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(
            {'detail': 'Successfully logged out.'},
            status=status.HTTP_200_OK,
        )


class UserProfileView(generics.RetrieveAPIView):
    """Return the authenticated user's own profile."""

    serializer_class = UserProfileSerializer

    def get_object(self):
        return self.request.user


# ---------------------------------------------------------------------------
# Admin-only user management views
# ---------------------------------------------------------------------------

class UserListCreateView(generics.ListCreateAPIView):
    """Admin-only: list all users or create a new user with any role."""

    queryset = User.objects.all()
    serializer_class = UserManagementSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdmin]


class UserDetailView(generics.RetrieveUpdateAPIView):
    """Admin-only: retrieve or update a user (role, active status, etc.)."""

    queryset = User.objects.all()
    serializer_class = UserManagementSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdmin]
