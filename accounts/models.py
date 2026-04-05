from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models


class CustomUserManager(UserManager):
    """Ensures superusers are automatically assigned the admin role."""

    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault('role', 'admin')
        return super().create_superuser(username, email, password, **extra_fields)


class User(AbstractUser):
    """
    Custom user model with a role field for role-based access control.
    Roles: viewer, analyst, admin.
    """

    class Role(models.TextChoices):
        VIEWER = 'viewer', 'Viewer'
        ANALYST = 'analyst', 'Analyst'
        ADMIN = 'admin', 'Admin'

    email = models.EmailField(unique=True, help_text='Unique email address.')

    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.VIEWER,
        help_text='User role for access control.',
    )

    objects = CustomUserManager()

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f'{self.username} ({self.get_role_display()})'
