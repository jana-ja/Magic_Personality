"""
Views der Social-App: fremde Profile ansehen (Task 3.1, FR-S1) und nach
Nickname suchen (Task 3.2, FR-S2).

Suche nach Farbkombination (3.3) und Freundschaften (3.4/3.5) kommen
mit den jeweils eigenen Tasks hinzu.
"""

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_GET

from apps.accounts import avatar
from apps.accounts.models import Profile


@login_required
@require_GET
def profile_detail(request, nickname):
    """
    FR-S1: Nickname, Profilbild, Bio, Farben — **nicht** Testhistorie,
    **nicht** E-Mail. `nickname__iexact` passend zur Eindeutigkeit
    case-insensitiv (FR-P2, `Profile.Meta.constraints`).

    `login_required` genügt für "nur für eingeloggte Nutzende
    sichtbar" — die Zugangssperre (D-09) gilt davor ohnehin für jede
    URL, das hier ist die zusätzliche Login-Pflicht aus FR-S1.
    """
    profile = get_object_or_404(Profile, nickname__iexact=nickname)
    assignment = profile.color_assignments.select_related("combination").first()

    context = {
        "profile": profile,
        "combination": assignment.combination if assignment else None,
        **avatar.avatar_context(assignment),
    }
    return render(request, "social/profile_detail.html", context)


@login_required
@require_GET
def search(request):
    """
    FR-S2: Teilstring-Suche nach Nickname, Groß-/Kleinschreibung egal.
    `login_required` aus demselben Grund wie bei `profile_detail` —
    Profile anderer (und damit auch ihre Nicknames) sind FR-S1 zufolge
    nur für Angemeldete sichtbar, die Suche macht davon keine Ausnahme.

    Leere oder fehlende Suchanfrage liefert keine Treffer statt aller
    Profile — ein leeres Suchfeld soll nicht versehentlich jeden
    Nickname auflisten.
    """
    query = request.GET.get("q", "").strip()
    results = []
    if query:
        results = Profile.objects.filter(nickname__icontains=query).order_by("nickname")

    context = {"query": query, "results": results}
    return render(request, "social/search.html", context)
