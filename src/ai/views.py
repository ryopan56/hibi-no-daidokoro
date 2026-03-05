import json
import logging

from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, transaction
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import AiDailyUsage, AiUsageLog
from .services.ai_client import AITimeoutError, AIClientError, OpenAIStructuredClient

logger = logging.getLogger(__name__)

DAILY_LIMIT = 3
RATE_LIMIT_MESSAGE = '本日のAI提案は上限（3回）に達しました。明日またお試しください。'
FALLBACK_MESSAGE = '現在AI提案が混み合っています。代わりに簡易案を表示します。'


FALLBACK_SUGGESTIONS = [
    {
        'title': '卵かけごはん + 味噌汁',
        'why': '短時間で作れて、軽く食べたい時に向いています。',
        'estimated_time_minutes': 10,
        'ingredients': ['ごはん', '卵', '味噌', 'だし'],
        'steps': ['味噌汁を作る', 'ごはんに卵をのせる'],
    },
    {
        'title': '納豆ごはん + 温野菜',
        'why': '手軽で、洗い物も少なく済みます。',
        'estimated_time_minutes': 12,
        'ingredients': ['ごはん', '納豆', '好みの野菜'],
        'steps': ['野菜を電子レンジで温める', '納豆を混ぜてごはんに添える'],
    },
    {
        'title': '豆腐とわかめのスープ',
        'why': '材料が少なく、胃に重くなりにくいです。',
        'estimated_time_minutes': 8,
        'ingredients': ['豆腐', 'わかめ', 'だし', '醤油'],
        'steps': ['鍋にだしを温める', '豆腐とわかめを入れて軽く煮る'],
    },
]


def _normalize_payload(raw_payload):
    payload = raw_payload if isinstance(raw_payload, dict) else {}

    available_ingredients = payload.get('available_ingredients')
    if not isinstance(available_ingredients, list):
        available_ingredients = []
    available_ingredients = [str(item) for item in available_ingredients if str(item).strip()]

    time_minutes = payload.get('time_minutes')
    try:
        time_minutes = int(time_minutes) if time_minutes is not None else None
    except (TypeError, ValueError):
        time_minutes = None

    taste_level = payload.get('taste_level')
    if taste_level not in {'light', 'normal', 'rich'}:
        taste_level = 'normal'

    notes = payload.get('notes')
    if notes is None:
        notes = ''
    notes = str(notes)[:200]

    return {
        'available_ingredients': available_ingredients,
        'time_minutes': time_minutes,
        'taste_level': taste_level,
        'notes': notes,
    }


def _normalize_suggestion(item):
    if not isinstance(item, dict):
        return {
            'title': '',
            'why': '',
            'estimated_time_minutes': None,
            'ingredients': [],
            'steps': [],
        }

    estimated_time = item.get('estimated_time_minutes')
    if not isinstance(estimated_time, int):
        estimated_time = None

    ingredients = item.get('ingredients')
    if not isinstance(ingredients, list):
        ingredients = []

    steps = item.get('steps')
    if not isinstance(steps, list):
        steps = []

    return {
        'title': str(item.get('title', '')),
        'why': str(item.get('why', '')),
        'estimated_time_minutes': estimated_time,
        'ingredients': [str(value) for value in ingredients],
        'steps': [str(value) for value in steps],
    }


def _suggestions_for_mode(mode, suggestions):
    normalized = [_normalize_suggestion(item) for item in suggestions]
    if mode == AiUsageLog.MODE_MINIMUM:
        return normalized[:2] or [_normalize_suggestion(FALLBACK_SUGGESTIONS[0])]
    return normalized[:3] if len(normalized) >= 2 else [_normalize_suggestion(item) for item in FALLBACK_SUGGESTIONS[:2]]


def _schema_response(status, mode, message, suggestions):
    return {
        'status': status,
        'mode': mode,
        'message': message,
        'suggestions': _suggestions_for_mode(mode, suggestions),
    }


def _fallback_response(mode):
    count = 1 if mode == AiUsageLog.MODE_MINIMUM else 2
    return _schema_response(
        status=AiUsageLog.STATUS_FALLBACK,
        mode=mode,
        message=FALLBACK_MESSAGE,
        suggestions=FALLBACK_SUGGESTIONS[:count],
    )


def _rate_limited_response(mode):
    count = 1 if mode == AiUsageLog.MODE_MINIMUM else 2
    return _schema_response(
        status=AiUsageLog.STATUS_RATE_LIMITED,
        mode=mode,
        message=RATE_LIMIT_MESSAGE,
        suggestions=FALLBACK_SUGGESTIONS[:count],
    )


def _save_usage_log(user, mode, jst_date, status, error_type=None):
    AiUsageLog.objects.create(
        user=user,
        mode=mode,
        jst_date=jst_date,
        status=status,
        error_type=error_type,
    )


def _lock_daily_usage(user, jst_date):
    for _ in range(2):
        try:
            daily_usage, created = AiDailyUsage.objects.select_for_update().get_or_create(
                user=user,
                jst_date=jst_date,
                defaults={'used_count': 0},
            )
            return daily_usage, created
        except IntegrityError:
            continue

    daily_usage = AiDailyUsage.objects.select_for_update().get(
        user=user,
        jst_date=jst_date,
    )
    return daily_usage, False


def _reserve_daily_quota(user, mode, jst_date):
    with transaction.atomic():
        daily_usage, created = _lock_daily_usage(user=user, jst_date=jst_date)
        if created:
            seed_count = AiUsageLog.objects.filter(
                user=user,
                jst_date=jst_date,
                status__in=[AiUsageLog.STATUS_OK, AiUsageLog.STATUS_FALLBACK],
            ).count()
            daily_usage.used_count = min(seed_count, DAILY_LIMIT)
            daily_usage.save(update_fields=['used_count', 'updated_at'])

        if daily_usage.used_count >= DAILY_LIMIT:
            payload = _rate_limited_response(mode)
            _save_usage_log(
                user=user,
                mode=mode,
                jst_date=jst_date,
                status=AiUsageLog.STATUS_RATE_LIMITED,
                error_type=None,
            )
            return False, payload

        daily_usage.used_count += 1
        daily_usage.save(update_fields=['used_count', 'updated_at'])
        return True, None


def _parse_json_request(request):
    content_type = request.headers.get('Content-Type', '')
    if 'application/json' not in content_type:
        raise ValueError('Content-Type must be application/json')

    try:
        return json.loads(request.body.decode('utf-8') or '{}')
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ValueError('Invalid JSON body') from exc


def _handle_ai_request(request, mode):
    jst_date = timezone.localdate()
    reserved, limited_payload = _reserve_daily_quota(user=request.user, mode=mode, jst_date=jst_date)
    if not reserved:
        return JsonResponse(limited_payload)

    try:
        request_payload = _normalize_payload(_parse_json_request(request))
    except ValueError as exc:
        logger.warning('ai request validation failed user=%s mode=%s error=%s', request.user.login_id, mode, exc)
        payload = _fallback_response(mode)
        _save_usage_log(
            user=request.user,
            mode=mode,
            jst_date=jst_date,
            status=AiUsageLog.STATUS_FALLBACK,
            error_type='validation',
        )
        return JsonResponse(payload)

    client = OpenAIStructuredClient()
    try:
        result = client.suggest(mode=mode, payload=request_payload)
        payload = _schema_response(
            status=AiUsageLog.STATUS_OK,
            mode=mode,
            message=str(result.get('message', 'AI提案を生成しました。')),
            suggestions=result.get('suggestions', []),
        )
        _save_usage_log(
            user=request.user,
            mode=mode,
            jst_date=jst_date,
            status=AiUsageLog.STATUS_OK,
            error_type=None,
        )
        return JsonResponse(payload)
    except AITimeoutError:
        logger.warning('ai request timeout user=%s mode=%s', request.user.login_id, mode)
        payload = _fallback_response(mode)
        _save_usage_log(
            user=request.user,
            mode=mode,
            jst_date=jst_date,
            status=AiUsageLog.STATUS_FALLBACK,
            error_type='timeout',
        )
        return JsonResponse(payload)
    except AIClientError as exc:
        logger.warning(
            'ai request client error user=%s mode=%s error_type=%s',
            request.user.login_id,
            mode,
            exc.error_type,
        )
        payload = _fallback_response(mode)
        _save_usage_log(
            user=request.user,
            mode=mode,
            jst_date=jst_date,
            status=AiUsageLog.STATUS_FALLBACK,
            error_type=exc.error_type,
        )
        return JsonResponse(payload)
    except Exception:
        logger.exception('ai request unexpected error user=%s mode=%s', request.user.login_id, mode)
        payload = _fallback_response(mode)
        _save_usage_log(
            user=request.user,
            mode=mode,
            jst_date=jst_date,
            status=AiUsageLog.STATUS_FALLBACK,
            error_type='unexpected',
        )
        return JsonResponse(payload)


@require_POST
@login_required
def ai_minimum(request):
    return _handle_ai_request(request, AiUsageLog.MODE_MINIMUM)


@require_POST
@login_required
def ai_recommend(request):
    return _handle_ai_request(request, AiUsageLog.MODE_RECOMMEND)
