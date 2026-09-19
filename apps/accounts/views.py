"""
Views der Accounts-App: Registrierung (Task 2.2), Account-Löschung
(Task 2.3), Profil ansehen/bearbeiten samt Profilbild (Task 2.4, 2.5),
Testhistorie (Task 2.12).

Login, Logout und Passwortänderung sind Djangos eigene Views
(`django.contrib.auth.views`), direkt in `urls.py` verdrahtet — dafür
gibt es keinen eigenen Code zu schreiben (ARCHITECTURE.md §7).
"""

from django.conf import settings
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods, require_POST

from apps.core.models import RegistrationAttempt
from apps.core.rate_limit import rate_limit
from apps.quiz.models import TestResult

from .forms import ColorsForm, RegistrationForm
from .models import Profile


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


@login_required
@require_http_methods(["GET", "POST"])
def delete_account(request):
    """
    FR-U8: vollständige Account-Löschung, mit ausdrücklicher
    Bestätigung — GET zeigt nur die Warnung, erst ein eigener POST
    löscht tatsächlich. `on_delete=CASCADE` (Task 2.1/2.6, D-22) erledigt
    den Rest: Profil, Farbzuordnung und Testhistorie hängen an `Profile`
    bzw. `User` und verschwinden mit ihm, ohne dass diese View sie
    einzeln anfassen muss.
    """
    if request.method == "POST":
        user = request.user
        user.delete()
        logout(request)
        return redirect(settings.LOGOUT_REDIRECT_URL)

    return render(request, "accounts/delete_account_confirm.html")


@login_required
@require_http_methods(["GET", "POST"])
def profile(request):
    """
    FR-P1/FR-P4: Speichern der Farben. Die Profilseite selbst ist seit Task
    4.1 (FR-P9, D-73) `/u/<nickname>/` — GET auf diese alte Adresse leitet
    dorthin weiter. POST speichert die Farbwahl (Nickname und Bio haben
    seit Task 4.5 eigene Endpunkte, Task 4.6 ersetzt auch diesen) und
    leitet zurück auf das Profil. `get_object_or_404` statt
    `request.user.profile`: ein per `createsuperuser` angelegter Account
    hat kein Profil (Task 0.2/2.1, D-22) — das ergibt hier eine klare 404
    statt eines Serverfehlers.
    """
    profile = get_object_or_404(Profile, user=request.user)
    if request.method == "POST":
        form = ColorsForm(request.POST, profile=profile)
        if form.is_valid():
            form.save()
    return redirect(profile)


@login_required
@require_POST
def delete_test_result(request, pk):
    """
    FR-P7/FR-P8: einzelne Historieneinträge sind löschbar. Referenziert
    `ColorAssignment.test_result` gerade diesen Eintrag, leert
    `on_delete=SET_NULL` (Task 2.1) automatisch nur die Referenz — die
    Profilfarben selbst bleiben unverändert bestehen, ohne dass diese
    View das selbst anfassen muss.
    """
    test_result = get_object_or_404(TestResult, pk=pk, profile__user=request.user)
    test_result.delete()
    return redirect("social:profile_history", nickname=test_result.profile.nickname)
