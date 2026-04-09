import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models


class Organization(models.Model):
    """Represents a participating organization in the federated network."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, unique=True)
    domain = models.CharField(max_length=253, blank=True)
    is_active = models.BooleanField(default=True)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class User(AbstractUser):
    """Custom user with SOC-specific roles and organization binding."""

    class Role(models.TextChoices):
        SECURITY_ANALYST = 'analyst', 'Security Analyst'
        NODE_ADMIN = 'node_admin', 'Node Administrator'
        SOC_MANAGER = 'soc_manager', 'SOC Manager'
        READONLY = 'readonly', 'Read-Only Viewer'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.SECURITY_ANALYST)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='members',
    )
    assigned_node = models.ForeignKey(
        'federated.FederatedNode',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='operators',
    )
    clearance_level = models.PositiveSmallIntegerField(
        default=1,
        help_text='Security clearance tier (1-5)',
    )
    mfa_enabled = models.BooleanField(default=False)
    last_activity = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['username']

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    @property
    def is_analyst(self):
        return self.role == self.Role.SECURITY_ANALYST

    @property
    def is_node_admin(self):
        return self.role == self.Role.NODE_ADMIN
