import logging
from datetime import date

from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from .forms import MealLogForm
from .models import MealLog

logger = logging.getLogger(__name__)


@require_http_methods(["GET", "POST"])
@login_required
def log_detail(request, log_date):
    try:
        parsed_date = date.fromisoformat(log_date)
    except ValueError as exc:
        raise Http404() from exc

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
        },
    )
    logger.info("meallog view end user=%s log_date=%s", request.user.login_id, log_date)
    return response
