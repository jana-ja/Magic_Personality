"""
Freundschaften (Task 3.4, FR-S4, D-20, D-22).

`Friendship` verweist auf `accounts.Profile`, nicht auf `accounts.User`
(D-22) — dieselbe Trennung wie bei `ColorAssignment`. Beidseitig und
bestätigungspflichtig (D-20): eine Zeile je Paar, mit Status PENDING
oder ACCEPTED und der Angabe, wer die Anfrage gestellt hat.

Kein zweiter Datensatz "aus der Sicht des anderen" — das Paar wird in
einer kanonischen Reihenfolge gespeichert (kleinere `Profile.pk`
zuerst, in `profile_a`), erzwungen über einen DB-Constraint. Das
verhindert sowohl eine doppelte Paarung in beiden Richtungen als auch
eine Freundschaft mit sich selbst in derselben Prüfung — ein Profil
kann nie eine kleinere UND eine größere PK als sich selbst haben.
`requested_by` bleibt trotzdem die tatsächliche Richtung der Anfrage,
unabhängig von der kanonischen Sortierung.
"""

from django.db import models
from django.db.models import CheckConstraint, F, Q, UniqueConstraint
from django.utils.translation import gettext_lazy as _


class FriendshipManager(models.Manager):
    def between(self, profile_a, profile_b):
        """Die (einzige) `Friendship`-Zeile zwischen zwei Profilen, oder
        `None` — unabhängig davon, in welcher Reihenfolge sie übergeben
        werden."""
        low, high = sorted([profile_a, profile_b], key=lambda profile: profile.pk)
        return self.filter(profile_a=low, profile_b=high).first()

    def for_profile(self, profile):
        """Alle Freundschaften/Anfragen, an denen `profile` beteiligt
        ist — gleich, ob als `profile_a` oder `profile_b`."""
        return self.filter(Q(profile_a=profile) | Q(profile_b=profile))


class Friendship(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", _("Pending")
        ACCEPTED = "ACCEPTED", _("Accepted")

    # Kanonisch sortiertes Paar (profile_a.pk < profile_b.pk, siehe
    # Meta.constraints) — keine feste Bedeutung wie "Sender"/"Empfänger",
    # nur eine feste Reihenfolge, damit dasselbe Paar immer dieselbe
    # Zeile trifft.
    profile_a = models.ForeignKey(
        "accounts.Profile", on_delete=models.CASCADE, related_name="friendships_as_a"
    )
    profile_b = models.ForeignKey(
        "accounts.Profile", on_delete=models.CASCADE, related_name="friendships_as_b"
    )
    # Die tatsächliche Richtung der Anfrage (FR-S4: "mit Angabe wer
    # angefragt hat") — unabhängig von profile_a/profile_b.
    requested_by = models.ForeignKey(
        "accounts.Profile", on_delete=models.CASCADE, related_name="sent_friend_requests"
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = FriendshipManager()

    class Meta:
        constraints = [
            # Keine doppelte Paarung in beiden Richtungen (FR-S4-DoD):
            # das Paar steht immer nur einmal, in kanonischer Reihenfolge.
            UniqueConstraint(fields=["profile_a", "profile_b"], name="unique_friendship_pair"),
            # Erzwingt die kanonische Reihenfolge selbst — und damit in
            # derselben Prüfung auch, dass profile_a != profile_b (keine
            # Freundschaft mit sich selbst, FR-S4-DoD): "a.pk < b.pk"
            # kann für a == b nie zutreffen.
            CheckConstraint(
                condition=Q(profile_a__lt=F("profile_b")), name="friendship_pair_ordered_no_self"
            ),
            # requested_by muss eine der beiden Parteien sein.
            CheckConstraint(
                condition=Q(requested_by=F("profile_a")) | Q(requested_by=F("profile_b")),
                name="friendship_requested_by_is_a_participant",
            ),
        ]

    def __str__(self):
        return f"{self.profile_a} <-> {self.profile_b} ({self.status})"

    def other_profile(self, profile):
        """Die jeweils andere Seite dieser Freundschaft, von `profile`
        aus gesehen."""
        return self.profile_b if self.profile_a_id == profile.pk else self.profile_a

    def involves(self, profile):
        return profile.pk in (self.profile_a_id, self.profile_b_id)
