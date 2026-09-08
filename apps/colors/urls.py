from django.urls import path

from . import views

app_name = "colors"

urlpatterns = [
    path("colors/", views.index, name="index"),
]
