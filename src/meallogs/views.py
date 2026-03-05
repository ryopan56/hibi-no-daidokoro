import logging
import calendar as py_calendar
from datetime import date

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods, require_POST

from .enums import IngredientCategory, TasteLevel
from .forms import MealLogForm, MealLogSearchForm
from .models import MealLog, MealLogIngredient, MealLogPhoto, MealLogTag, Tag

logger = logging.getLogger(__name__)

MAX_PHOTOS_PER_LOG = 10
MAX_TAG_CANDIDATES = 20
DEFAULT_TAG_KIND = "general"


def _parse_log_date(log_date):
    try:
        return date.fromisoformat(log_date)
    except ValueError as exc:
        raise Http404() from exc


def _get_meallog_for_user(user, parsed_date):
    meallog, created = MealLog.objects.get_or_create(
        user=user,
        log_date=parsed_date,
    )
    return meallog, created


def _build_keyword_condition(keyword):
    condition = Q(tags__name__icontains=keyword) | Q(tags__kind__icontains=keyword)
    matched_categories = [
        value
        for value, label in IngredientCategory.choices
        if keyword.casefold() in str(label).casefold()
    ]
    if matched_categories:
        condition |= Q(ingredients__category__in=matched_categories)

    matched_taste_levels = [
        value
        for value, label in TasteLevel.choices()
        if keyword.casefold() in str(label).casefold()
        or keyword.casefold() == TasteLevel.to_code(value).casefold()
    ]
    if matched_taste_levels:
        condition |= Q(taste_level__in=matched_taste_levels)

    if keyword.isdigit():
        condition |= Q(time_minutes=int(keyword))

    return condition


def _parse_year_month(query_params):
    today = date.today()
    raw_year = query_params.get("year")
    raw_month = query_params.get("month")

    if raw_year is None and raw_month is None:
        return today.year, today.month

    try:
        year = int(raw_year)
        month = int(raw_month)
        date(year, month, 1)
    except (TypeError, ValueError):
        return today.year, today.month

    return year, month


@require_http_methods(["GET", "POST"])
@login_required
def log_detail(request, log_date):
    parsed_date = _parse_log_date(log_date)

    logger.info("meallog view start user=%s log_date=%s", request.user.login_id, log_date)

    meallog, created = _get_meallog_for_user(request.user, parsed_date)
    logger.info(
        "meallog get_or_create user=%s log_date=%s created=%s",
        request.user.login_id,
        log_date,
        created,
    )

    if request.method == "POST":
        form = MealLogForm(request.POST, instance=meallog)
        if form.is_valid():
            before = {
                "time_minutes": meallog.time_minutes,
                "taste_level": meallog.taste_level,
            }
            before_categories = set(meallog.ingredients.values_list("category", flat=True))
            before["ingredient_categories"] = sorted(before_categories)
            form.save()
            selected_categories = set(form.cleaned_data.get("ingredient_categories") or [])
            to_add = selected_categories - before_categories
            to_remove = before_categories - selected_categories
            if to_add:
                MealLogIngredient.objects.bulk_create(
                    [MealLogIngredient(meal_log=meallog, category=value) for value in to_add],
                    ignore_conflicts=True,
                )
            if to_remove:
                meallog.ingredients.filter(category__in=to_remove).delete()
            after_categories = set(meallog.ingredients.values_list("category", flat=True))
            after = {
                "time_minutes": meallog.time_minutes,
                "taste_level": meallog.taste_level,
                "ingredient_categories": sorted(after_categories),
            }
            logger.info(
                "meallog save user=%s log_date=%s before=%s after=%s",
                request.user.login_id,
                log_date,
                before,
                after,
            )
            logger.info("meallog view end user=%s log_date=%s", request.user.login_id, log_date)
            return redirect("meallog_detail", log_date=log_date)

        logger.info(
            "meallog validation error user=%s log_date=%s errors=%s",
            request.user.login_id,
            log_date,
            form.errors.as_json(),
        )
    else:
        form = MealLogForm(
            instance=meallog,
            initial={
                "ingredient_categories": list(
                    meallog.ingredients.values_list("category", flat=True)
                )
            },
        )

    candidates = (
        Tag.objects.filter(meal_logs__user=request.user)
        .distinct()
        .order_by("kind", "name")[:MAX_TAG_CANDIDATES]
    )

    response = render(
        request,
        "meallogs/log_detail.html",
        {
            "form": form,
            "log_date": parsed_date,
            "photos": meallog.photos.all(),
            "tags": meallog.tags.all().order_by("kind", "name"),
            "ingredient_categories": meallog.ingredients.all().order_by("category"),
            "tag_candidates": candidates,
            "default_tag_kind": DEFAULT_TAG_KIND,
        },
    )
    logger.info("meallog view end user=%s log_date=%s", request.user.login_id, log_date)
    return response


@require_http_methods(["GET", "POST"])
@login_required
def search_logs(request):
    form = MealLogSearchForm(request.POST or None)
    meallogs = MealLog.objects.none()
    searched = False

    if request.method == "POST" and form.is_valid():
        q = (form.cleaned_data.get("q") or "").strip()
        date_from = form.cleaned_data.get("date_from")
        date_to = form.cleaned_data.get("date_to")
        keywords = [keyword for keyword in q.split() if keyword]

        if keywords or date_from or date_to:
            searched = True
            queryset = MealLog.objects.filter(user=request.user)
            if date_from:
                queryset = queryset.filter(log_date__gte=date_from)
            if date_to:
                queryset = queryset.filter(log_date__lte=date_to)
            for keyword in keywords:
                queryset = queryset.filter(_build_keyword_condition(keyword))

            meallogs = queryset.distinct().order_by("-log_date")

    return render(
        request,
        "meallogs/search.html",
        {
            "form": form,
            "meallogs": meallogs,
            "searched": searched,
        },
    )


@require_http_methods(["GET"])
@login_required
def calendar_view(request):
    year, month = _parse_year_month(request.GET)
    _, last_day = py_calendar.monthrange(year, month)
    month_start = date(year, month, 1)
    month_end = date(year, month, last_day)

    logged_dates = set(
        MealLog.objects.filter(
            user=request.user,
            log_date__gte=month_start,
            log_date__lte=month_end,
        ).values_list("log_date", flat=True)
    )

    weeks = []
    for week in py_calendar.Calendar(firstweekday=6).monthdatescalendar(year, month):
        week_cells = []
        for day in week:
            week_cells.append(
                {
                    "date": day,
                    "in_month": day.month == month,
                    "has_log": day in logged_dates,
                }
            )
        weeks.append(week_cells)

    prev_year = year - 1 if month == 1 else year
    prev_month = 12 if month == 1 else month - 1
    next_year = year + 1 if month == 12 else year
    next_month = 1 if month == 12 else month + 1

    return render(
        request,
        "meallogs/calendar.html",
        {
            "display_year": year,
            "display_month": month,
            "month_label": f"{year}年{month}月",
            "day_names": ["日", "月", "火", "水", "木", "金", "土"],
            "weeks": weeks,
            "prev_year": prev_year,
            "prev_month": prev_month,
            "next_year": next_year,
            "next_month": next_month,
        },
    )


@require_POST
@login_required
def upload_photos(request, log_date):
    parsed_date = _parse_log_date(log_date)
    files = request.FILES.getlist("photos")

    logger.info(
        "meallog upload start user=%s log_date=%s files_count=%s",
        request.user.login_id,
        log_date,
        len(files),
    )

    meallog, created = _get_meallog_for_user(request.user, parsed_date)
    logger.info(
        "meallog get_or_create user=%s log_date=%s created=%s",
        request.user.login_id,
        log_date,
        created,
    )

    existing_count = meallog.photos.count()
    if existing_count + len(files) > MAX_PHOTOS_PER_LOG:
        logger.info(
            "meallog upload too many user=%s log_date=%s existing=%s new=%s",
            request.user.login_id,
            log_date,
            existing_count,
            len(files),
        )
        messages.error(request, "写真は1日10枚までです。減らしてからもう一度お試しください。")
        return redirect("meallog_detail", log_date=log_date)

    if not files:
        messages.error(request, "写真が選択されていません。")
        return redirect("meallog_detail", log_date=log_date)

    try:
        for upload in files:
            MealLogPhoto.objects.create(meal_log=meallog, image=upload)
    except Exception:
        logger.exception(
            "meallog upload error user=%s log_date=%s",
            request.user.login_id,
            log_date,
        )
        messages.error(request, "写真の保存に失敗しました。時間をおいて再度お試しください。")
        return redirect("meallog_detail", log_date=log_date)

    logger.info(
        "meallog upload end user=%s log_date=%s files_count=%s",
        request.user.login_id,
        log_date,
        len(files),
    )
    return redirect("meallog_detail", log_date=log_date)


@require_POST
@login_required
def delete_photo(request, photo_id):
    logger.info("meallog delete start user=%s photo_id=%s", request.user.login_id, photo_id)
    try:
        photo = MealLogPhoto.objects.select_related("meal_log").get(
            id=photo_id,
            meal_log__user=request.user,
        )
    except MealLogPhoto.DoesNotExist as exc:
        logger.error(
            "meallog delete forbidden user=%s photo_id=%s",
            request.user.login_id,
            photo_id,
        )
        raise Http404() from exc

    photo.delete()
    logger.info("meallog delete end user=%s photo_id=%s", request.user.login_id, photo_id)
    return redirect("meallog_detail", log_date=photo.meal_log.log_date.isoformat())


@require_POST
@login_required
def add_tag(request, log_date):
    parsed_date = _parse_log_date(log_date)
    tag_name = request.POST.get("tag_name", "").strip()
    tag_kind = request.POST.get("tag_kind", DEFAULT_TAG_KIND).strip()

    logger.info(
        "meallog tag add start user=%s log_date=%s kind=%s name=%s",
        request.user.login_id,
        log_date,
        tag_kind,
        tag_name,
    )

    if not tag_name:
        logger.info(
            "meallog tag validation error user=%s log_date=%s reason=empty",
            request.user.login_id,
            log_date,
        )
        messages.error(request, "タグ名を入力してください。")
        return redirect("meallog_detail", log_date=log_date)

    if len(tag_name) > 64 or len(tag_kind) > 32:
        logger.info(
            "meallog tag validation error user=%s log_date=%s reason=length",
            request.user.login_id,
            log_date,
        )
        messages.error(request, "タグ名が長すぎます。短くして再度お試しください。")
        return redirect("meallog_detail", log_date=log_date)

    meallog, created = _get_meallog_for_user(request.user, parsed_date)
    logger.info(
        "meallog get_or_create user=%s log_date=%s created=%s",
        request.user.login_id,
        log_date,
        created,
    )

    tag, _ = Tag.objects.get_or_create(kind=tag_kind, name=tag_name)
    MealLogTag.objects.get_or_create(meal_log=meallog, tag=tag)

    logger.info(
        "meallog tag add end user=%s log_date=%s kind=%s name=%s",
        request.user.login_id,
        log_date,
        tag_kind,
        tag_name,
    )
    return redirect("meallog_detail", log_date=log_date)


@require_POST
@login_required
def delete_tag(request, log_date, tag_id):
    parsed_date = _parse_log_date(log_date)

    logger.info(
        "meallog tag delete start user=%s log_date=%s tag_id=%s",
        request.user.login_id,
        log_date,
        tag_id,
    )

    meallog = get_object_or_404(MealLog, user=request.user, log_date=parsed_date)

    try:
        link = MealLogTag.objects.select_related("tag", "meal_log").get(
            meal_log=meallog,
            tag_id=tag_id,
        )
    except MealLogTag.DoesNotExist as exc:
        logger.info(
            "meallog tag delete forbidden user=%s log_date=%s tag_id=%s",
            request.user.login_id,
            log_date,
            tag_id,
        )
        raise Http404() from exc

    link.delete()
    logger.info(
        "meallog tag delete end user=%s log_date=%s tag_id=%s",
        request.user.login_id,
        log_date,
        tag_id,
    )
    return redirect("meallog_detail", log_date=log_date)
