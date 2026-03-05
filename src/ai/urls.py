from django.urls import path

from . import views

urlpatterns = [
    path('minimum', views.ai_minimum, name='ai_minimum'),
    path('recommend', views.ai_recommend, name='ai_recommend'),
]
