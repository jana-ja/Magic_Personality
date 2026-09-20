"""
Mengengrenzen je Person (Task 5.3, FR-B11, D-78).

Anders als Gate, Registrierung und Feedback (D-75) gibt es keine eigene
Zähltabelle mit IP-Adressen: Wer schreibt, ist angemeldet, der richtige
Schlüssel ist die Person. Gezählt wird aus deren eigenen Zeilen — ein
Beitrag, den die Person gelöscht hat, zählt danach nicht mehr mit; bei den
Grenzen (30 Beiträge, 60 Kommentare, 20 Meldungen je Stunde) ist das
hinnehmbar und spart die Buchführung.
"""

from django.utils import timezone


def is_limited(own_rows, *, max_count, window_seconds):
    """
    True, wenn `own_rows` (ein QuerySet der eigenen Zeilen mit `created_at`)
    im Zeitfenster schon `max_count` oder mehr enthält.
    """
    since = timezone.now() - timezone.timedelta(seconds=window_seconds)
    return own_rows.filter(created_at__gte=since).count() >= max_count
