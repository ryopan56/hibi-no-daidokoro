import uuid
from pathlib import Path as SysPath

from django.conf import settings
from django.db import models

from .enums import TasteLevel


def meal_log_photo_upload_to(instance, filename):
    ext = SysPath(filename).suffix.lower()
    name = f"{uuid.uuid4().hex}{ext}"
    log_date = instance.meal_log.log_date.isoformat()
    return f"meallogs/{instance.meal_log.user_id}/{log_date}/{name}"


class MealLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    log_date = models.DateField()
    time_minutes = models.PositiveSmallIntegerField(null=True, blank=True)
    taste_level = models.PositiveSmallIntegerField(
        choices=TasteLevel.choices(),
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "log_date"], name="uniq_user_log_date"),
        ]

    def __str__(self) -> str:
        return f"{self.user_id}:{self.log_date}"


class MealLogPhoto(models.Model):
    meal_log = models.ForeignKey(
        MealLog,
        on_delete=models.CASCADE,
        related_name="photos",
    )
    image = models.ImageField(upload_to=meal_log_photo_upload_to)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
