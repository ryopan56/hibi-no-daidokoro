from datetime import timedelta

from django.utils import timezone

from meallogs.models import MealLog

from accounts.models import NotificationSettings
from accounts.services.weekly_praise import (
    WEEKLY_PRAISE_FALLBACK,
    WeeklyPraiseError,
    WeeklyPraiseTimeoutError,
    generate_weekly_praise,
)


def current_week_start_jst():
    today_local = timezone.localdate()
    days_since_sunday = (today_local.weekday() + 1) % 7
    return today_local - timedelta(days=days_since_sunday)


def get_or_create_notification_settings(user):
    settings_obj, _ = NotificationSettings.objects.get_or_create(user=user)
    return settings_obj


def _build_weekly_praise_payload(user, current_week_start):
    period_start = current_week_start - timedelta(days=7)
    period_end = current_week_start - timedelta(days=1)
    meallogs = (
        MealLog.objects.filter(
            user=user,
            log_date__gte=period_start,
            log_date__lte=period_end,
        )
        .prefetch_related('tags')
        .order_by('log_date')
    )

    logs = []
    for meallog in meallogs:
        logs.append(
            {
                'log_date': meallog.log_date.isoformat(),
                'result': None,
                'cook_granularity': None,
                'minimum_mode': None,
                'comment': None,
                'weather': None,
                'temp_feel': None,
                'tags': list(meallog.tags.values_list('name', flat=True)),
            }
        )

    return {
        'feature': 'weekly_praise',
        'period': {
            'start_date': period_start.isoformat(),
            'end_date': period_end.isoformat(),
        },
        'logs': logs,
    }


def _get_or_generate_weekly_praise(settings_obj, user, current_week_start):
    if (
        settings_obj.last_weekly_praise_generated_week_start == current_week_start
        and isinstance(settings_obj.weekly_praise_payload_json, dict)
    ):
        return settings_obj.weekly_praise_payload_json

    payload = _build_weekly_praise_payload(user=user, current_week_start=current_week_start)
    try:
        generated = generate_weekly_praise(payload)
        settings_obj.weekly_praise_status = NotificationSettings.PRAISE_STATUS_OK
    except (WeeklyPraiseError, WeeklyPraiseTimeoutError):
        generated = WEEKLY_PRAISE_FALLBACK
        settings_obj.weekly_praise_status = NotificationSettings.PRAISE_STATUS_FALLBACK

    settings_obj.last_weekly_praise_generated_week_start = current_week_start
    settings_obj.weekly_praise_payload_json = generated
    settings_obj.save(
        update_fields=[
            'last_weekly_praise_generated_week_start',
            'weekly_praise_payload_json',
            'weekly_praise_status',
            'updated_at',
        ]
    )
    return generated


def consume_weekly_praise_for_home(user):
    settings_obj = get_or_create_notification_settings(user)
    current_week_start = current_week_start_jst()

    if not settings_obj.weekly_praise_enabled:
        return None, settings_obj

    if settings_obj.last_weekly_praise_shown_week_start == current_week_start:
        return None, settings_obj

    weekly_praise = _get_or_generate_weekly_praise(
        settings_obj=settings_obj,
        user=user,
        current_week_start=current_week_start,
    )

    settings_obj.last_weekly_praise_shown_week_start = current_week_start
    settings_obj.save(update_fields=['last_weekly_praise_shown_week_start', 'updated_at'])
    return weekly_praise, settings_obj
