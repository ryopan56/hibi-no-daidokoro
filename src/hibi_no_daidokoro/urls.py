from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

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
    path('logs/<log_date>/photos', meallogs_views.upload_photos, name='meallog_upload_photos'),
    path('photos/<int:photo_id>/delete', meallogs_views.delete_photo, name='meallog_delete_photo'),
    path('admin/', admin.site.urls),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
