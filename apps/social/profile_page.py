"""
Kontext der Profilseite (Task 4.1, FR-P9, D-73).

Eigenes und fremdes Profil sind dieselbe Seite (`/u/<nickname>/`); dieser
Baustein trägt zusammen, was das Template dafür braucht. Bewusst
kein View-Code: sowohl `apps.social.views.profile_detail` als auch die
(noch bestehende) Sammel-Speichern-View in `apps.accounts.views` bauen
damit dieselbe Seite — die zweite nur, um Formularfehler auf derselben
Vorlage anzuzeigen, bis Task 4.5 die Bereiche einzeln bearbeitbar macht.
"""

from apps.accounts import avatar
from apps.accounts.forms import ProfileForm
from apps.colors.content import LOCALE
from apps.colors.models import ColorCombination

from . import friendships
from .models import Friendship


def relationship_context(viewer_profile, other_profile):
    """
    FR-S4: der aktuelle Stand zwischen zwei Profilen. `relationship` ist
    eine von `None` (keine Beziehung), `"pending_sent"` (ich habe
    angefragt), `"pending_received"` (die andere Person hat angefragt)
    oder `"friends"`.
    """
    friendship = Friendship.objects.between(viewer_profile, other_profile)
    if friendship is None:
        return {"friendship": None, "relationship": None}
    if friendship.status == Friendship.Status.ACCEPTED:
        relationship = "friends"
    elif friendship.requested_by_id == viewer_profile.pk:
        relationship = "pending_sent"
    else:
        relationship = "pending_received"
    return {"friendship": friendship, "relationship": relationship}


def history_with_combinations(profile, assignment):
    """
    FR-P6: Historie mit Datum, Punkten und Ergebnis. `TestResult` kennt
    nur `result_colors` (den Code), keinen Fremdschlüssel auf
    `ColorCombination` — die Namen werden hier in einer Abfrage
    nachgeladen statt je Eintrag einzeln und direkt an die Instanzen
    gehängt, damit das Template nicht selbst nachschlagen muss. Ebenso
    `is_adopted`: ob die Profilfarben gerade auf genau diesen Eintrag
    verweisen (FR-P5) — das Template zeigt dort statt des
    Übernehmen-Knopfs einen Hinweis.
    """
    results = list(profile.test_results.all())
    combinations_by_code = {
        combination.code: combination
        for combination in ColorCombination.objects.filter(
            locale=LOCALE, code__in={result.result_colors for result in results}
        )
    }
    for result in results:
        result.combination = combinations_by_code[result.result_colors]
        result.is_adopted = assignment is not None and assignment.test_result_id == result.pk
    return results


def profile_context(profile, viewer_profile, *, form=None):
    """
    Kontext für `social/profile_detail.html`. `is_owner` schaltet die
    Bearbeiten-Zugänge und alles Private ein (Formular, offene
    Anfragen, Testhistorie, Account löschen) — sonst der
    Freundschaftsstatus zur angesehenen Person (FR-S4).

    `form`: ein bereits gebundenes `ProfileForm` (mit Fehlern) für die
    Anzeige nach einem fehlgeschlagenen Speichern.

    Die Punkte des übernommenen Testergebnisses (D-70) zeigt die Seite
    allen, weder Datum noch die übrige Historie (D-19).
    """
    assignment = profile.color_assignments.select_related("combination", "test_result").first()
    test_result = assignment.test_result if assignment else None
    is_owner = viewer_profile.pk == profile.pk

    context = {
        "profile": profile,
        "is_owner": is_owner,
        "combination": assignment.combination if assignment else None,
        "test_scores": test_result.ordered_scores if test_result else None,
        "friends": friendships.accepted_friends(profile),
        **avatar.avatar_context(assignment),
    }
    if not is_owner:
        context.update(relationship_context(viewer_profile, profile))
        return context

    if form is None:
        form = ProfileForm(
            initial={
                "nickname": profile.nickname,
                "bio": profile.bio,
                "colors": list(assignment.combination.code) if assignment else [],
            },
            profile=profile,
        )
    context.update(
        {
            "form": form,
            "test_results": history_with_combinations(profile, assignment),
            # FR-S4: offene Anfragen in beide Richtungen.
            "friend_requests_received": friendships.pending_requests_received(profile),
            "friend_requests_sent": friendships.pending_requests_sent(profile),
        }
    )
    return context
