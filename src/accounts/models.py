from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.conf import settings
from django.db import models
from django.utils import timezone


class CustomUserManager(BaseUserManager):
    def create_user(self, login_id, password=None, **extra_fields):
        if not login_id:
            raise ValueError('login_id is required')

        user = self.model(login_id=login_id, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, login_id, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(login_id=login_id, password=password, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    login_id = models.CharField(max_length=150, unique=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    objects = CustomUserManager()

    USERNAME_FIELD = 'login_id'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.login_id


class NotificationSettings(models.Model):
    PRAISE_STATUS_OK = 'ok'
    PRAISE_STATUS_FALLBACK = 'fallback'
    PRAISE_STATUS_CHOICES = [
        (PRAISE_STATUS_OK, 'ok'),
        (PRAISE_STATUS_FALLBACK, 'fallback'),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notification_settings',
    )
    notifications_enabled = models.BooleanField(default=True)
    weekly_praise_enabled = models.BooleanField(default=True)
    last_weekly_praise_shown_week_start = models.DateField(null=True, blank=True)
    last_weekly_praise_generated_week_start = models.DateField(null=True, blank=True)
    weekly_praise_payload_json = models.JSONField(null=True, blank=True)
    weekly_praise_status = models.CharField(
        max_length=16,
        choices=PRAISE_STATUS_CHOICES,
        null=True,
        blank=True,
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'notification_settings'
