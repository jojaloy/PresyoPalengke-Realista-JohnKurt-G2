from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Custom user: Django's built-in auth (hashed passwords) plus a role and profile fields."""

    class Role(models.TextChoices):
        SHOPPER = 'shopper', 'Shopper'
        VENDOR = 'vendor', 'Vendor'
        ADMIN = 'admin', 'Admin'

    email = models.EmailField('email address', unique=True)
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.SHOPPER)
    contact_number = models.CharField(max_length=20, blank=True)
    preferred_markets = models.CharField(
        max_length=255, blank=True,
        help_text='Markets you visit often (e.g. Carbon Market, Bulacao Market).',
    )
    profile_photo = models.ImageField(upload_to='profile_photos/', blank=True, null=True)

    def save(self, *args, **kwargs):
        # Normalise email so uniqueness is case-insensitive in practice.
        if self.email:
            self.email = self.email.strip().lower()
        # Superusers (createsuperuser) are Admins.
        if self.is_superuser:
            self.role = self.Role.ADMIN
        super().save(*args, **kwargs)

    @property
    def is_shopper(self):
        return self.role == self.Role.SHOPPER

    @property
    def is_vendor(self):
        return self.role == self.Role.VENDOR

    @property
    def is_admin_role(self):
        return self.role == self.Role.ADMIN

    def __str__(self):
        return f'{self.username} ({self.get_role_display()})'
