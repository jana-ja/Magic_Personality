"""Views der Accounts-App: Registrierung (Task 2.2).

Login, Logout und Passwortänderung sind Djangos eigene Views
(`django.contrib.auth.views`), direkt in `urls.py` verdrahtet — dafür
gibt es keinen eigenen Code zu schreiben (ARCHITECTURE.md §7).
"""

from django.conf import settings
from django.contrib.auth import login
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from apps.core.models import RegistrationAttempt
from apps.core.rate_limit import rate_limit

from .forms import RegistrationForm


@require_http_methods(["GET", "POST"])
@rate_limit(
    RegistrationAttempt,
    max_attempts=settings.REGISTRATION_RATE_LIMIT_MAX_ATTEMPTS,
    window_seconds=settings.REGISTRATION_RATE_LIMIT_WINDOW_SECONDS,
)
def register(request):
    """
    FR-U1: Voraussetzung ist ein gültiger Invite-Code — das prüft
    bereits `GateMiddleware` für jede URL dieser Anwendung (D-09),
    diese View braucht dafür keine eigene Prüfung.
    """
    if request.user.is_authenticated:
        return redirect(settings.LOGIN_REDIRECT_URL)

    form = RegistrationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user, _profile = form.save()
        # Direkt anmelden statt zum Login zu schicken — mit mehreren
        # AUTHENTICATION_BACKENDS (Task 2.2, django-axes) muss login()
        # das Backend explizit genannt bekommen.
        login(request, user, backend="django.contrib.auth.backends.ModelBackend")
        return redirect(settings.LOGIN_REDIRECT_URL)

    return render(request, "accounts/register.html", {"form": form})
