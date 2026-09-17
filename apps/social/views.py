"""
Views der Social-App: fremde Profile ansehen (Task 3.1, FR-S1).

Suche (3.2/3.3) und Freundschaften (3.4/3.5) kommen mit den jeweils
eigenen Tasks hinzu.
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
