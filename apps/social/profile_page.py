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
from apps.accounts.forms import BioForm, ColorsForm, NicknameForm
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


PINBOARD = "pinboard"
FRIENDS = "friends"
HISTORY = "history"
SETTINGS = "settings"


def profile_context(profile, viewer_profile, *, tab=PINBOARD, editing=None, edit_form=None):
    """
    Kontext für die Profilseite und ihre Tabs (Task 4.1/4.3, FR-P9,
    FR-P11, D-73). Gemeinsam für jeden Tab: Kopfbereich (Farben,
    Freundschaftsaktion), Tab-Leiste und — nur für die eigene Person —
    die Zahl offener Anfragen am Tab „Friends".

    `is_owner` schaltet die Bearbeiten-Zugänge und alles Private ein.
    `tab`: `PINBOARD` (Standard, bei der eigenen Person mit dem
    Bearbeiten-Formular), `FRIENDS` (Freundesliste, bei der eigenen Person
    zusätzlich die offenen Anfragen) sowie die nur der eigenen Person
    vorbehaltenen `HISTORY` (Testhistorie) und `SETTINGS` (Einstellungen) —
    die beiden rufen nur Views auf, die vorher `owner_only` passiert haben.

    `editing` (`"nickname"` oder `"bio"`, Task 4.5) schaltet den jeweiligen
    Bereich der Seite in den Bearbeiten-Modus, `edit_form` ist dessen
    (ggf. gebundenes, fehlerhaftes) Formular.

    Die Punkte des übernommenen Testergebnisses (D-70) zeigt die Seite
    allen, weder Datum noch die übrige Historie (D-19).
    """
    assignment = profile.color_assignments.select_related("combination", "test_result").first()
    test_result = assignment.test_result if assignment else None
    is_owner = viewer_profile.pk == profile.pk

    context = {
        "profile": profile,
        "is_owner": is_owner,
        "active_tab": tab,
        "combination": assignment.combination if assignment else None,
        "test_scores": test_result.ordered_scores if test_result else None,
        **avatar.avatar_context(assignment),
    }
    received = []
    if is_owner:
        received = list(friendships.pending_requests_received(profile))
        context["friend_request_count"] = len(received)
    else:
        context.update(relationship_context(viewer_profile, profile))

    if tab == FRIENDS:
        context["friends"] = friendships.accepted_friends(profile)
        if is_owner:
            context["friend_requests_received"] = received
            context["friend_requests_sent"] = friendships.pending_requests_sent(profile)
        return context

    if tab == HISTORY:
        context["test_results"] = history_with_combinations(profile, assignment)
        return context

    if tab == SETTINGS:
        return context

    if is_owner:
        context["editing"] = editing
        context["edit_form"] = edit_form
        context["colors_form"] = ColorsForm(
            initial={"colors": list(assignment.combination.code) if assignment else []},
            profile=profile,
        )
    return context


def edit_form_for(section, profile, data=None):
    """Das Formular zu einem Bearbeiten-Bereich (Task 4.5): `"nickname"`
    oder `"bio"`, ungebunden mit dem aktuellen Wert oder gebunden an `data`."""
    if section == "nickname":
        if data is None:
            return NicknameForm(initial={"nickname": profile.nickname}, profile=profile)
        return NicknameForm(data, profile=profile)
    if data is None:
        return BioForm(initial={"bio": profile.bio}, profile=profile)
    return BioForm(data, profile=profile)
