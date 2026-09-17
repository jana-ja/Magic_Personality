"""
Freundschafts-Logik (Task 3.4, FR-S4; Freundeslisten Task 3.5, FR-S5,
FR-S6). Reine Funktionen auf `Friendship`, getrennt von den Views: dort
steht nur noch, welches Profil aus der URL geladen wird und wohin am
Ende umgeleitet wird — hier steht, was mit einer Freundschaft zwischen
zwei Profilen erlaubt ist und wer wessen Freund ist.

`PermissionDenied` statt eines stillen No-Ops, wenn eine unbeteiligte
Person eine Aktion versucht (Roadmap-Test: "nicht von Dritten
angenommen werden") — Views lassen das unbehandelt durch, Django
antwortet darauf serienmäßig mit 403.
"""

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction
from django.utils.translation import gettext_lazy as _

from .models import Friendship


def send_request(requester, target):
    """
    FR-S4: Anfrage senden. `IntegrityError` (Constraint aus
    `Friendship.Meta`) wird zu einer `ValidationError` — sowohl eine
    bereits offene Anfrage als auch eine bestehende Freundschaft
    zwischen denselben beiden Profilen lösen das gleichermaßen aus
    (Roadmap-Test: "Anfrage kann nicht doppelt gestellt werden").

    Das `create()` steht in einem eigenen `atomic()`-Block: Postgres
    markiert die laufende Transaktion nach einem `IntegrityError` als
    kaputt, bis zum nächsten Savepoint zurückgerollt wird — ohne den
    eigenen Block würde jede weitere Abfrage in derselben Transaktion
    (z. B. der aufrufenden View oder einem Test) mit
    `TransactionManagementError` fehlschlagen, statt nur diesen einen
    Versuch abzuweisen.
    """
    if requester.pk == target.pk:
        raise ValidationError(_("You cannot send a friend request to yourself."))

    profile_a, profile_b = sorted([requester, target], key=lambda profile: profile.pk)
    try:
        with transaction.atomic():
            return Friendship.objects.create(
                profile_a=profile_a,
                profile_b=profile_b,
                requested_by=requester,
                status=Friendship.Status.PENDING,
            )
    except IntegrityError:
        raise ValidationError(
            _("There is already a friendship or a pending request between these profiles.")
        ) from None


def _require_participant(friendship, acting_profile):
    if not friendship.involves(acting_profile):
        raise PermissionDenied("Not a participant in this friendship.")


def accept_request(friendship, acting_profile):
    """
    FR-S4: Anfrage annehmen — nur durch die Empfängerin, nicht durch
    die anfragende Person selbst und nicht durch Dritte (Roadmap-Test).
    """
    _require_participant(friendship, acting_profile)
    if friendship.status != Friendship.Status.PENDING:
        raise ValidationError(_("This request is no longer pending."))
    if acting_profile.pk == friendship.requested_by_id:
        raise PermissionDenied("Only the recipient can accept a friend request.")

    friendship.status = Friendship.Status.ACCEPTED
    friendship.save(update_fields=["status"])
    return friendship


def decline_request(friendship, acting_profile):
    """
    FR-S4: Anfrage ablehnen. Beide Seiten dürfen das — die Empfängerin
    lehnt ab, die anfragende Person zieht ihre eigene Anfrage zurück.
    Beides löscht dieselbe offene Zeile, es gibt keinen dritten Status
    dafür.
    """
    _require_participant(friendship, acting_profile)
    if friendship.status != Friendship.Status.PENDING:
        raise ValidationError(_("This request is no longer pending."))

    friendship.delete()


def dissolve(friendship, acting_profile):
    """FR-S4: bestehende Freundschaft auflösen — durch jede der beiden
    Seiten."""
    _require_participant(friendship, acting_profile)
    if friendship.status != Friendship.Status.ACCEPTED:
        raise ValidationError(_("This friendship is not active."))

    friendship.delete()


def pending_requests_received(profile):
    """Offene Anfragen an `profile` (FR-S4/Task 3.4-DoD: im eigenen
    Profil sichtbar) — andere haben sie gestellt, `profile` entscheidet."""
    return (
        Friendship.objects.for_profile(profile)
        .filter(status=Friendship.Status.PENDING)
        .exclude(requested_by=profile)
        .select_related("profile_a", "profile_b", "requested_by")
        .order_by("created_at")
    )


def pending_requests_sent(profile):
    """
    Offene Anfragen, die `profile` selbst gestellt hat und die noch
    auf eine Antwort warten. Hängt die jeweils andere Seite als
    `.other` an jede Zeile — `Friendship.other_profile()` nimmt ein
    Argument und ist damit aus dem Template heraus nicht aufrufbar
    (Django-Templates rufen nur parameterlose Methoden über den
    Attributzugriff auf, wie `_test_results_with_combinations` in
    `apps.accounts.views` es für `.combination` genauso macht).
    """
    requests = list(
        Friendship.objects.for_profile(profile)
        .filter(status=Friendship.Status.PENDING, requested_by=profile)
        .select_related("profile_a", "profile_b")
        .order_by("created_at")
    )
    for friendship in requests:
        friendship.other = friendship.other_profile(profile)
    return requests


def accepted_friends(profile):
    """
    FR-S5/FR-S6: die bestätigten Freundschaften von `profile`, als
    Liste der jeweils *anderen* Profile — fürs Anzeigen (eigene
    Freundesliste, Task 3.5, und dieselbe Funktion für die Freundes-
    liste eines fremden Profils, FR-S6) reicht das, es gibt keinen
    Grund, dafür die `Friendship`-Zeile selbst durchzureichen.
    """
    friendship_rows = (
        Friendship.objects.for_profile(profile)
        .filter(status=Friendship.Status.ACCEPTED)
        .select_related("profile_a", "profile_b")
    )
    friends = [friendship.other_profile(profile) for friendship in friendship_rows]
    friends.sort(key=lambda friend: friend.nickname.lower())
    return friends
