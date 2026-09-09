from django.urls import path

from . import views

urlpatterns = [
    path("healthz", views.healthz, name="healthz"),
    path("gate/", views.gate, name="gate"),
    path("robots.txt", views.robots_txt, name="robots_txt"),
    # Task 1.11: beide liegen bewusst *nicht* auf der Gate-Ausnahmeliste
    # (apps.core.gate.EXEMPT_EXACT_PATHS) — FR-A1 kennt keine Ausnahme,
    # "About" und "Privacy" eingeschlossen.
    path("about/", views.about, name="about"),
    path("privacy/", views.privacy, name="privacy"),
]
