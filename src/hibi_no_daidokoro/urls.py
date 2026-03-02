from django.contrib import admin
from django.urls import path

from accounts import views as accounts_views
from meallogs import views as meallogs_views

urlpatterns = [
    path('', accounts_views.home, name='home'),
    path('home/', accounts_views.home, name='home'),
    path('signup/', accounts_views.signup, name='signup'),
    path('login/', accounts_views.login_view, name='login'),
    path('logout/', accounts_views.logout_view, name='logout'),
    path('logs/today/', accounts_views.today_logs, name='logs_today'),
    path('logs/<log_date>/', meallogs_views.log_detail, name='meallog_detail'),
    path('admin/', admin.site.urls),
]
