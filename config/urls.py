"""
URL-Konfiguration.

Fachliche URLs (Auth, Quiz, Social) kommen mit den jeweiligen Tasks
in docs/ROADMAP.md hinzu; Color Infos liegen seit Task 1.5 unter
/colors/. Das Invite-Gate aus Task 0.5
setzt an, bevor irgendeine dieser URLs erreichbar ist.
"""

from django.contrib import admin
from django.urls import include, path, reverse_lazy
from django.views.generic.base import RedirectView

urlpatterns = [
    path("admin/", admin.site.urls),
    # "/" selbst hat noch keine eigene Seite (kein v0.1-Feature sieht
    # das vor) — ohne diese Route landet man nach dem Gate-Login hier
    # (apps.core.gate.safe_next_url() fällt genau darauf zurück) und
    # bekäme einen 404. Temporär (302), nicht kanonisch: anders als
    # die Redirects in Task 1.6 (dieselbe Ressource unter einer
    # anderen URL) ist hier noch keine eigene Ressource da, die sich
    # später ändern könnte, sobald Accounts/Quiz eine echte Startseite
    # brauchen.
    path("", RedirectView.as_view(url=reverse_lazy("colors:index")), name="home"),
    path("", include("apps.colors.urls")),
    path("", include("apps.core.urls")),
    path("accounts/", include("apps.accounts.urls")),
    path("", include("apps.quiz.urls")),
    path("", include("apps.social.urls")),
    path("", include("apps.posts.urls")),
]
