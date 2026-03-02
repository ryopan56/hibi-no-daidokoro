import logging
from datetime import date

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods, require_POST

from .forms import MealLogForm
from .models import MealLog, MealLogPhoto

logger = logging.getLogger(__name__)

MAX_PHOTOS_PER_LOG = 10


def _parse_log_date(log_date):
    try:
        return date.fromisoformat(log_date)
    except ValueError as exc:
        raise Http404() from exc


@require_http_methods(["GET", "POST"])
@login_required
def log_detail(request, log_date):
    parsed_date = _parse_log_date(log_date)

    logger.info("meallog view start user=%s log_date=%s", request.user.login_id, log_date)

    meallog, created = MealLog.objects.get_or_create(
        user=request.user,
        log_date=parsed_date,
    )
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
            form.save()
            after = {
                "time_minutes": meallog.time_minutes,
                "taste_level": meallog.taste_level,
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
        form = MealLogForm(instance=meallog)

    response = render(
        request,
        "meallogs/log_detail.html",
        {
            "form": form,
            "log_date": parsed_date,
            "photos": meallog.photos.all(),
        },
    )
    logger.info("meallog view end user=%s log_date=%s", request.user.login_id, log_date)
    return response


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

    meallog, created = MealLog.objects.get_or_create(
        user=request.user,
        log_date=parsed_date,
    )
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
