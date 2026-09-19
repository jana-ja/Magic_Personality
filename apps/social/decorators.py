"""
Decorator für „nur die eigene Person"-Seiten des Profils (Task 4.4, D-73).

Private Adressen (`/u/<nickname>/history/`, `/settings/`, später die
Bearbeiten-Adressen aus 4.5/4.6) leiten jede **andere** Person auf das
öffentliche Profil der Adresse weiter, statt 404 oder 403 zu liefern. Die
Adresse verrät nichts, was nicht ohnehin öffentlich wäre: das Profil ist für
Angemeldete sichtbar und die privaten Tabs gibt es bei jedem Profil gleich.
Die Entscheidung fällt hier an einer Stelle, damit sie nicht je Seite neu
getroffen wird.
"""

from functools import wraps

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect

from apps.accounts.models import Profile


def owner_only(view):
    """
    Umhüllt einen View `view(request, profile, ...)`, der unter einer
    Adresse mit `<nickname>` hängt. Reihenfolge der Entscheidungen:
    Gäste zum Login (`login_required`), unbekannter Nickname 404, andere
    Person 302 auf `/u/<nickname>/` ohne jeden Inhalt der privaten Seite,
    nur die eigene Person erreicht den View — der bekommt das Profil statt
    des Nicknames. Gilt für jede HTTP-Methode: auch ein POST einer anderen
    Person wird weitergeleitet und verändert nichts.
    """

    @wraps(view)
    @login_required
    def wrapper(request, nickname, *args, **kwargs):
        profile = get_object_or_404(Profile, nickname__iexact=nickname)
        viewer_profile = get_object_or_404(Profile, user=request.user)
        if viewer_profile.pk != profile.pk:
            return redirect(profile)
        return view(request, profile, *args, **kwargs)

    return wrapper
