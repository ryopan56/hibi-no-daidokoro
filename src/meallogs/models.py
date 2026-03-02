from django.conf import settings
from django.db import models

from .enums import TasteLevel


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
