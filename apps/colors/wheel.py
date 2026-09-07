"""
Farbrad-Geometrie und -Beziehungen (Task 1.2, FR-C9, D-04).

Bewusst rein und Django-unabhängig: alles hier arbeitet mit einfachen
Radpositionen (0..4), nicht mit Farbcodes oder Modellen. Genau eine
Konstante — POSITION_COUNT — treibt Nachbarschaft, Feindschaft und
SVG-Koordinaten an; sie stimmen dadurch immer überein.

Die Brücke zu echten Farben zieht ColorCombination.relation in
apps/colors/models.py: dort werden Farbcodes über Color.wheel_position
in Positionen übersetzt (ARCHITECTURE.md §6.3 — "reine Berechnung aus
wheel_position"), bevor die Funktionen hier ins Spiel kommen.
"""

import math

#: Fünf Farben, fünf Positionen im Kreis (FR-C1).
POSITION_COUNT = 5


def _circular_distance(position_a, position_b):
    """Kürzester Abstand zwischen zwei Positionen auf dem Kreis."""
    raw_distance = abs(position_a - position_b) % POSITION_COUNT
    return min(raw_distance, POSITION_COUNT - raw_distance)


def are_neighbors(position_a, position_b):
    """True, wenn zwei Positionen direkt nebeneinander liegen (Ally, D-04)."""
    return _circular_distance(position_a, position_b) == 1


def are_enemies(position_a, position_b):
    """
    True, wenn zwei Positionen einander gegenüberliegend genug sind, um
    Feinde zu sein (D-04). Bei fünf Positionen ist das jeder
    Nicht-Nachbar außer der Position selbst — ein anderer Abstand als
    1 oder 2 kann im Fünferrad gar nicht vorkommen.
    """
    return position_a != position_b and not are_neighbors(position_a, position_b)


def wheel_coordinates(position, *, radius=1.0, center=(0.0, 0.0), start_angle_deg=-90.0):
    """
    (x, y) für eine Radposition auf einem Kreis mit `radius` um
    `center`, in SVG-Koordinaten (y wächst nach unten).

    Position 0 liegt bei `start_angle_deg` (Standard: oben, negative
    y-Achse — FR-C1: "Spitze nach oben"). Weil SVG die y-Achse
    gegenüber der üblichen Mathematik-Konvention spiegelt, erzeugt ein
    einfaches Aufaddieren des Winkels hier bereits eine Bewegung im
    Uhrzeigersinn — kein zusätzliches Spiegeln nötig (durch einen Test
    gegen die erwartete Richtung abgesichert).
    """
    angle_deg = start_angle_deg + (360 / POSITION_COUNT) * position
    angle_rad = math.radians(angle_deg)
    x = center[0] + radius * math.cos(angle_rad)
    y = center[1] + radius * math.sin(angle_rad)
    return x, y
