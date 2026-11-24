"""
Punkte je Farbe als Balken (Task 4.7, D-70, NFR-6).

Gemeinsamer Baustein für die Colors-Karte im Profil
(`templates/social/_card_colors.html`) und die Ergebnisseite des Tests
(`templates/quiz/result.html`); das Markup dazu steht in
`templates/colors/_score_bars.html`. Liegt in `apps.colors`, weil er nur
Farben kennt — weder Profil noch Test.
"""

from . import pentagon
from .models import Color


def ordered_scores(scores):
    """`(Farbcode, Punkte)` in WUBRG-Reihenfolge aus einem `scores`-Dict
    (wie `tally()` es liefert oder `TestResult.scores` es speichert).
    Fehlende Farben zählen mit 0 Punkten."""
    return [(code, scores.get(code, 0)) for code, _label in Color.Code.choices]


def score_bars(ordered):
    """
    Buchstabe **und** Zahl stehen dabei, der Balken ist nur zusätzliche
    Anschauung, die Farbe kein alleiniger Unterschied (NFR-6). Länge
    relativ zum höchsten Wert der Verteilung. Die Balkenfarbe ist die
    Halo-Farbe der Ecke (Weiß wäre als `Color.hex` auf hellem Grund kaum
    zu sehen, D-42).
    """
    colors = {color.code: color for color in Color.objects.all()}
    top = max((points for _code, points in ordered), default=0) or 1
    return [
        {
            "code": code,
            "name": colors[code].name,
            "points": points,
            "percent": round(points / top * 100),
            "color": pentagon.halo_color(code, colors[code].hex),
        }
        for code, points in ordered
    ]
