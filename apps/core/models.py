"""
Modelle der Core-App.

GateAttempt zählt Versuche an der Zugangssperre (Task 0.5),
RegistrationAttempt Versuche an der Registrierung (Task 2.2, FR-U6),
FeedbackAttempt Absendungen des Feedback-Formulars (Task 4.11, FR-T18) —
alle drei reine Rate-Limiting-Buchführung, keine fachlichen Daten. Zeilen
wachsen bei 3–10 Nutzenden extrem langsam; eine Aufräumroutine ist
deshalb bewusst kein Teil dieser Tasks.
"""

from django.db import models


class GateAttempt(models.Model):
    """Ein Versuch, den Invite-Code einzugeben — unabhängig vom Ergebnis."""

    ip_address = models.GenericIPAddressField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["ip_address", "created_at"]),
        ]

    def __str__(self):
        return f"{self.ip_address} @ {self.created_at:%Y-%m-%d %H:%M:%S}"


class RegistrationAttempt(models.Model):
    """Ein Registrierungsversuch — unabhängig vom Ergebnis (Task 2.2)."""

    ip_address = models.GenericIPAddressField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["ip_address", "created_at"]),
        ]

    def __str__(self):
        return f"{self.ip_address} @ {self.created_at:%Y-%m-%d %H:%M:%S}"


class FeedbackAttempt(models.Model):
    """Eine Absendung des Feedback-Formulars — unabhängig vom Ergebnis (Task 4.11)."""

    ip_address = models.GenericIPAddressField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["ip_address", "created_at"]),
        ]

    def __str__(self):
        return f"{self.ip_address} @ {self.created_at:%Y-%m-%d %H:%M:%S}"
