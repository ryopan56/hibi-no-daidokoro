from django.conf import settings
from django.db import models


class AiUsageLog(models.Model):
    MODE_MINIMUM = 'minimum'
    MODE_RECOMMEND = 'recommend'
    MODE_CHOICES = [
        (MODE_MINIMUM, 'minimum'),
        (MODE_RECOMMEND, 'recommend'),
    ]

    STATUS_OK = 'ok'
    STATUS_FALLBACK = 'fallback'
    STATUS_RATE_LIMITED = 'rate_limited'
    STATUS_CHOICES = [
        (STATUS_OK, 'ok'),
        (STATUS_FALLBACK, 'fallback'),
        (STATUS_RATE_LIMITED, 'rate_limited'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='ai_usage_logs',
    )
    mode = models.CharField(max_length=16, choices=MODE_CHOICES)
    jst_date = models.DateField(db_index=True)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES)
    error_type = models.CharField(max_length=32, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'ai_usage_logs'
        ordering = ['-created_at']


class AiDailyUsage(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='ai_daily_usages',
    )
    jst_date = models.DateField()
    used_count = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'ai_daily_usages'
        constraints = [
            models.UniqueConstraint(fields=['user', 'jst_date'], name='uniq_ai_daily_usage_user_date')
        ]
