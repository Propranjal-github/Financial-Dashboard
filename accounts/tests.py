from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


class AuthTestCase(APITestCase):
    """Tests for login (JWT), logout, and profile endpoints."""

    def setUp(self):
        self.login_url = '/api/v1/auth/login/'
        self.logout_url = '/api/v1/auth/logout/'
        self.profile_url = '/api/v1/auth/profile/'

    def test_login_success(self):
        User.objects.create_user(username='testuser', email='testuser@example.com', password='StrongPass123!')
        response = self.client.post(self.login_url, {
            'username': 'testuser',
            'password': 'StrongPass123!',
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_login_invalid_credentials(self):
        response = self.client.post(self.login_url, {
            'username': 'nouser',
            'password': 'wrong',
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # ---- Logout ----

    def test_logout_success(self):
        user = User.objects.create_user(username='testuser', email='testuser@example.com', password='StrongPass123!')
        refresh = RefreshToken.for_user(user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        response = self.client.post(self.logout_url, {'refresh': str(refresh)})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_logout_missing_token(self):
        user = User.objects.create_user(username='testuser', email='testuser@example.com', password='StrongPass123!')
        self.client.force_authenticate(user=user)
        response = self.client.post(self.logout_url, {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # ---- Profile ----

    def test_profile_authenticated(self):
        user = User.objects.create_user(username='testuser', email='testuser@example.com', password='StrongPass123!')
        self.client.force_authenticate(user=user)
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'testuser')

    def test_profile_unauthenticated(self):
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class RolePermissionTestCase(APITestCase):
    """Tests for role-based access control on user management endpoints."""

    def setUp(self):
        self.admin = User.objects.create_user(
            username='admin', email='admin@example.com', password='AdminPass123!', role='admin',
        )
        self.analyst = User.objects.create_user(
            username='analyst', email='analyst@example.com', password='AnalystPass123!', role='analyst',
        )
        self.viewer = User.objects.create_user(
            username='viewer', email='viewer@example.com', password='ViewerPass123!', role='viewer',
        )
        self.users_url = '/api/v1/auth/users/'

    def test_admin_can_list_users(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.users_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_viewer_cannot_list_users(self):
        self.client.force_authenticate(user=self.viewer)
        response = self.client.get(self.users_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_analyst_cannot_list_users(self):
        self.client.force_authenticate(user=self.analyst)
        response = self.client.get(self.users_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_create_user(self):
        self.client.force_authenticate(user=self.admin)
        data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'role': 'analyst',
            'password': 'NewPass123!',
        }
        response = self.client.post(self.users_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.get(username='newuser').role, 'analyst')

    def test_admin_can_deactivate_user(self):
        self.client.force_authenticate(user=self.admin)
        url = f'{self.users_url}{self.viewer.pk}/'
        response = self.client.patch(url, {'is_active': False})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.viewer.refresh_from_db()
        self.assertFalse(self.viewer.is_active)
