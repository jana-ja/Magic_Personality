"""
Auswahl-Logik für die Fünfeck-Selektion (Task 1.6, FR-C4 bis FR-C7).

Reine Funktionen auf Farbcode-Mengen — kein Zugriff auf Modelle,
Request oder URLs. Legt eine Sache fest, die `apps/colors/utils.py`
noch offenlässt: die URL-Form ist kleingeschrieben
(`"wu"`, nicht `"WU"`), auch wenn `ColorCombination.code` selbst
großgeschrieben ist. PRD §5.2 (FR-C7) und Roadmap 1.6 schreiben das
so in ihren Beispielen vor (`/colors/wu`, Redirect-Beispiel
`/colors/uw/`).
"""

from . import utils


def parse_url_code(raw_code):
    """
    `raw_code` (der `<code>`-Teil der URL) zu einer Menge von
    Farbcodes ("W".."G"). `None`, wenn `raw_code` keine gültige
    Farbmenge beschreibt — Buchstaben außerhalb WUBRG, ein doppelt
    vorkommender Buchstabe oder mehr als fünf Zeichen (Roadmap 1.6:
    "Ungültige Codes ergeben 404"). Groß-/Kleinschreibung im Input ist
    hier egal, das prüft `canonical_url_code` bzw. der Aufrufer.
    """
    letters = raw_code.upper()
    if not 1 <= len(letters) <= 5:
        return None
    if len(set(letters)) != len(letters):
        return None
    if not set(letters) <= set(utils.CANONICAL_ORDER):
        return None
    return set(letters)


def canonical_url_code(colors):
    """Die kanonische URL-Form einer Farbmenge, z. B. {"U", "W"} -> "wu"."""
    return utils.canonical_code(colors).lower()


def toggled(selected_colors, color_code):
    """Die Farbmenge nach dem Umschalten von `color_code` (FR-C4)."""
    if color_code in selected_colors:
        return selected_colors - {color_code}
    return selected_colors | {color_code}
