import logging

from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods, require_POST

from .forms import LoginForm, SignupForm

logger = logging.getLogger(__name__)


@require_http_methods(["GET", "POST"])
def signup(request):
    if request.method == "POST":
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_login(request, user)
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
    return render(request, "accounts/home.html")
