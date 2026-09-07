"""
Reine Farbcode-Hilfsfunktionen — unabhängig von Geometrie und
Nachbarschaft (die kommt mit Task 1.2, Farbrad-Logik). Hier geht es
nur um die kanonische WUBRG-Sortierung, die `ColorCombination.code`
zugrunde liegt (D-27, ARCHITECTURE.md §6.2).
"""

CANONICAL_ORDER = "WUBRG"


def canonical_code(colors):
    """
    Baut aus einer Menge/Sequenz von Farbcodes (z. B. "UW", ["U", "W"])
    den kanonisch in WUBRG-Reihenfolge sortierten, deduplizierten Code
    ("WU"). Unbekannte Buchstaben werden stillschweigend verworfen —
    `is_canonical` macht daraus die passende Ablehnung.
    """
    unique_colors = set(colors)
    return "".join(color for color in CANONICAL_ORDER if color in unique_colors)


def is_canonical(code):
    """True, wenn `code` bereits genau die kanonische Form ist."""
    return code == canonical_code(code)
