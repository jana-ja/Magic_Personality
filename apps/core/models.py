"""
Modelle der Core-App.

GateAttempt zählt Versuche an der Zugangssperre (Task 0.5) — reine
Rate-Limiting-Buchführung, keine fachlichen Daten. Zeilen wachsen bei
3–10 Nutzenden extrem langsam; eine Aufräumroutine ist deshalb bewusst
kein Teil dieses Tasks.
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
