"""
URL-Konfiguration.

Fachliche URLs (Color Infos, Auth, Quiz, Social) kommen mit den
jeweiligen Tasks in docs/ROADMAP.md hinzu. Das Invite-Gate aus Task 0.5
setzt an, bevor irgendeine dieser URLs erreichbar ist.
"""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("apps.core.urls")),
]
