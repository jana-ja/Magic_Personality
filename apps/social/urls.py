from django.urls import path

from . import views

app_name = "social"

urlpatterns = [
    path("u/<str:nickname>/", views.profile_detail, name="profile_detail"),
]
