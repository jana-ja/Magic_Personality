"""
Generiertes Profilbild (Task 2.5, FR-P3, D-13).

Bis zu fünf gleich breite, senkrechte Streifen — je einer pro
hinterlegter Farbe, in der kanonischen WUBRG-Reihenfolge von
`ColorCombination.code` (D-27). Ohne hinterlegte Farben ein einzelner
neutraler Streifen (Task 2.5: "neutrale Darstellung"). Reine Geometrie
plus ein schlanker DB-Zugriff auf `Color.hex` — kein Upload, keine
Dateiablage, das Bild entsteht bei jedem Rendern neu (D-13).

Der Kreis selbst kommt nicht aus einem SVG-`clipPath` (dessen `id`
kollidieren würde, sobald eine Seite mehrere Avatare gleichzeitig zeigt
— Task 3.1/3.5), sondern aus `border-radius: 50%` auf dem `<svg>`-
Wurzelelement selbst (`static/css/base.css`, `.avatar`).

Aufbau bewusst wie `apps/colors/pentagon.py`: Geometrie/Daten hier,
Farben selbst ausschließlich über CSS-Klassen mit einer inline
gesetzten Custom Property je Segment (wie `pentagon.Vertex.halo`/
`--halo`) — nicht als hartes `fill`-Attribut.
"""

from dataclasses import dataclass

from apps.colors.models import Color

VIEW_BOX = "0 0 100 100"


@dataclass(frozen=True)
class Segment:
    x: float
    width: float
    hex: str


def segments(color_codes, hex_by_code=None):
    """
    `color_codes`: Sequenz von Farbcodes, z. B. `["W", "U"]` — schon in
    der gewünschten Reihenfolge, typischerweise
    `ColorCombination.color_codes` (kanonisch WUBRG-sortiert). Leer,
    wenn ein Profil keine hinterlegten Farben hat — die neutrale
    Darstellung übernimmt dann `templates/accounts/_avatar.html`.
    """
    if not color_codes:
        return []

    if hex_by_code is None:
        hex_by_code = dict(Color.objects.filter(code__in=color_codes).values_list("code", "hex"))
    width = 100 / len(color_codes)
    return [
        Segment(x=index * width, width=width, hex=hex_by_code[code])
        for index, code in enumerate(color_codes)
    ]


def avatar_context(color_assignment, hex_by_code=None):
    """
    Kontext für den Avatar-Baustein (`templates/accounts/_avatar.html`).
    `color_assignment`: die `ColorAssignment` des Profils oder `None`
    (kein Datensatz -> neutrale Darstellung, siehe Task 2.5s DoD).
    `hex_by_code`: optional die Farbwerte, wenn der Aufrufer viele Bilder
    rendert und sie einmal geladen hat (Autorenkarten, Task 4.8) — sonst
    fragt jedes Bild sie selbst ab.
    """
    color_codes = color_assignment.combination.color_codes if color_assignment else []
    return {"segments": segments(color_codes, hex_by_code), "view_box": VIEW_BOX}
