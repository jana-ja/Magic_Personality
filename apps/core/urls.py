from django.urls import path

from . import views

urlpatterns = [
    path("healthz", views.healthz, name="healthz"),
    path("gate/", views.gate, name="gate"),
    path("robots.txt", views.robots_txt, name="robots_txt"),
]
