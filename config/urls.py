"""
URL-Konfiguration.

Fachliche URLs (Auth, Quiz, Social) kommen mit den jeweiligen Tasks
in docs/ROADMAP.md hinzu; Color Infos liegen seit Task 1.5 unter
/colors/. Das Invite-Gate aus Task 0.5
setzt an, bevor irgendeine dieser URLs erreichbar ist.
"""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("apps.colors.urls")),
    path("", include("apps.core.urls")),
]
