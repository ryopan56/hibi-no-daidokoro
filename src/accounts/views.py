import logging
from datetime import date

from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods, require_POST

from .forms import LoginForm, NotificationSettingsForm, SignupForm
from .services.weekly_praise_trigger import (
    consume_weekly_praise_for_home,
    get_or_create_notification_settings,
)

logger = logging.getLogger(__name__)

WELCOME_SHOWN_DATE_KEY = 'welcome_shown_date'
JUST_LOGGED_IN_KEY = 'just_logged_in'


@require_http_methods(["GET", "POST"])
def signup(request):
    if request.method == "POST":
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_login(request, user)
            request.session[JUST_LOGGED_IN_KEY] = True
            logger.info("signup success login_id=%s", user.login_id)
            return redirect("home")
        logger.info(
            "signup failed login_id=%s errors=%s",
            request.POST.get("login_id", ""),
            form.errors.as_json(),
        )
    else:
        form = SignupForm()

    return render(request, "accounts/signup.html", {"form": form})


@require_http_methods(["GET", "POST"])
def login_view(request):
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            login_id = form.cleaned_data["login_id"]
            password = form.cleaned_data["password"]
            user = authenticate(request, login_id=login_id, password=password)
            if user is not None:
                auth_login(request, user)
                request.session[JUST_LOGGED_IN_KEY] = True
                logger.info("login success login_id=%s", login_id)
                return redirect("home")

            logger.info("login failed login_id=%s", login_id)
            form.add_error(None, "ログインに失敗しました。もう一度お試しください。")
        else:
            logger.info("login failed login_id=%s", request.POST.get("login_id", ""))
            form.add_error(None, "ログインに失敗しました。もう一度お試しください。")
    else:
        form = LoginForm()

    return render(request, "accounts/login.html", {"form": form})


@require_POST
def logout_view(request):
    login_id = request.user.login_id if request.user.is_authenticated else ""
    auth_logout(request)
    logger.info("logout login_id=%s", login_id)
    return redirect("login")


@login_required
def home(request):
    today_str = date.today().isoformat()
    welcome_shown_date = request.session.get(WELCOME_SHOWN_DATE_KEY)
    just_logged_in = request.session.get(JUST_LOGGED_IN_KEY, False)

    show_welcome = welcome_shown_date != today_str or just_logged_in
    if show_welcome:
        request.session[WELCOME_SHOWN_DATE_KEY] = today_str
        request.session[JUST_LOGGED_IN_KEY] = False
    weekly_praise, _ = consume_weekly_praise_for_home(request.user)

    logger.info(
        "home access login_id=%s welcome=%s",
        request.user.login_id,
        show_welcome,
    )

    return render(
        request,
        "accounts/home.html",
        {
            "show_welcome": show_welcome,
            "weekly_praise": weekly_praise,
        },
    )


@login_required
def today_logs(request):
    logger.info("today redirect login_id=%s", request.user.login_id)
    return render(request, "accounts/today.html")


@require_http_methods(["GET", "POST"])
@login_required
def notification_settings(request):
    settings_obj = get_or_create_notification_settings(request.user)
    if request.method == "POST":
        form = NotificationSettingsForm(request.POST, instance=settings_obj)
        if form.is_valid():
            form.save()
            messages.success(request, "通知設定を更新しました。")
            return redirect("notification_settings")
    else:
        form = NotificationSettingsForm(instance=settings_obj)

    return render(
        request,
        "accounts/notification_settings.html",
        {"form": form},
    )
