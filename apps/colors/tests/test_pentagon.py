"""
Tests für das SVG-Layout des Fünfecks (Task 1.5, FR-C1 bis FR-C3).

Prüft die Geometrie, nicht das Aussehen: dass die Ecken dort liegen,
wo die Farbrad-Logik aus Task 1.2 sie hinrechnet, dass Reihenfolge und
Ausrichtung stimmen und dass nichts aus dem Bildausschnitt ragt.
"""

import pytest

from apps.colors import pentagon, wheel
from apps.colors.models import Color, ColorCombination, PerspectivePole

pytestmark = pytest.mark.django_db


@pytest.fixture
def vertices():
    return pentagon.vertices(Color.objects.all())


def _view_box(vertices):
    min_x, min_y, width, height = (float(value) for value in pentagon.view_box(vertices).split())
    return min_x, min_y, min_x + width, min_y + height


# Reihenfolge und Ausrichtung (FR-C1) ---------------------------------------


def test_the_colors_run_clockwise_from_white_at_the_top(vertices):
    assert [vertex.code for vertex in vertices] == ["W", "U", "B", "R", "G"]


def test_white_sits_at_the_top_point(vertices):
    white = vertices[0]

    assert white.x == pytest.approx(pentagon.CENTER[0])
    assert white.y < pentagon.CENTER[1]


def test_the_order_around_the_figure_is_clockwise(vertices):
    """
    Im Uhrzeigersinn heißt in SVG-Koordinaten (y wächst nach unten):
    nach der Spitze geht es nach rechts, dann nach unten, dann nach
    links zurück.
    """
    white, blue, black, red, green = vertices

    assert blue.x > white.x and blue.y > white.y
    assert black.x > pentagon.CENTER[0] and black.y > blue.y
    assert red.x < pentagon.CENTER[0] and red.y == pytest.approx(black.y)
    assert green.x < red.x and green.y < red.y


# Koordinaten kommen aus der Farbrad-Logik, nicht aus festen Werten ----------


def test_every_vertex_comes_from_wheel_coordinates(vertices):
    for vertex in vertices:
        position = Color.objects.get(code=vertex.code).wheel_position
        expected = wheel.wheel_coordinates(
            position, radius=pentagon.VERTEX_RADIUS, center=pentagon.CENTER
        )
        assert (vertex.x, vertex.y) == pytest.approx(expected)


def test_all_vertices_lie_on_one_circle_around_the_centre(vertices):
    distances = [
        ((vertex.x - pentagon.CENTER[0]) ** 2 + (vertex.y - pentagon.CENTER[1]) ** 2) ** 0.5
        for vertex in vertices
    ]
    assert distances == pytest.approx([pentagon.VERTEX_RADIUS] * 5)


# Linien --------------------------------------------------------------------


def _pairs_from(points, vertices):
    """Die Punktliste zurück auf Farbcodes abbilden, paarweise."""
    by_position = {(round(v.x, 3), round(v.y, 3)): v.code for v in vertices}
    codes = [by_position[tuple(float(n) for n in point.split(","))] for point in points.split()]
    return [(codes[index], codes[(index + 1) % len(codes)]) for index in range(len(codes))]


def _positions(code_pair):
    return [Color.objects.get(code=code).wheel_position for code in code_pair]


def test_the_outline_connects_allied_colors(vertices):
    for pair in _pairs_from(pentagon.outline_points(vertices), vertices):
        assert wheel.are_neighbors(*_positions(pair)), pair


def test_the_star_connects_enemy_colors(vertices):
    pairs = _pairs_from(pentagon.star_points(vertices), vertices)

    assert len(pairs) == 5
    for pair in pairs:
        assert wheel.are_enemies(*_positions(pair)), pair


# Bildausschnitt ------------------------------------------------------------


def test_nothing_sticks_out_of_the_view_box(vertices):
    """Symbol und Name jeder Ecke liegen vollständig im Fenster."""
    min_x, min_y, max_x, max_y = _view_box(vertices)

    outside = {
        vertex.name: vertex.bounds
        for vertex in vertices
        if not (
            vertex.bounds[0] >= min_x
            and vertex.bounds[1] >= min_y
            and vertex.bounds[2] <= max_x
            and vertex.bounds[3] <= max_y
        )
    }
    assert outside == {}


def test_the_view_box_is_centred_horizontally(vertices):
    """
    Sonst sitzt die Figur sichtbar außermittig, weil "Green" links
    weiter hinausragt als "Blue" rechts.
    """
    min_x, _, max_x, _ = _view_box(vertices)

    # abs statt der viel engeren Standardtoleranz: view_box() rundet
    # auf drei Nachkommastellen (ein SVG-Attribut, keine
    # Berechnungsgrundlage mehr) — min_x und max_x können dadurch bis
    # zu 0.001 auseinanderrunden, obwohl sie vor dem Runden exakt
    # symmetrisch aus demselben half_width gebildet werden.
    assert min_x == pytest.approx(-max_x, abs=0.002)


def test_a_longer_color_name_widens_the_view_box(vertices):
    """
    Der Ausschnitt ist berechnet, nicht eingetragen — eine Übersetzung
    mit längeren Namen (D-15) darf nicht abgeschnitten werden.
    """
    before = _view_box(vertices)

    Color.objects.filter(code="U").update(name="Blue" * 5)
    after = _view_box(pentagon.vertices(Color.objects.all()))

    assert after[2] > before[2]


# Pol-/Theme-Label-Breite (D-49) ---------------------------------------
#
# `pentagon._label_width()` schätzt die Pill-Breite aus der Zeichenzahl
# (LABEL_CHAR_WIDTH) statt echte Schriftmetriken zu kennen — dieselbe
# grundsätzliche Ungenauigkeit wie bei Vertex.bounds (Kommentar dort),
# nur mit einer eigenen, großzügigeren Konstante, weil Pol-/Theme-Text
# kursiv bzw. fett gesetzt ist und mehrwortige Sätze statt einzelner
# Farbnamen trägt (D-49).
#
# MEASURED_*_TEXT_WIDTHS ist die unabhängige Gegenprobe: die echte,
# im Browser gemessene Breite (SVG `getComputedTextLength()`, mit
# genau dem Stil aus base.css — kursiv fürs Pol-, fett fürs
# Theme-Label, System-UI-Font) für jeden Pol- und Theme-Text, der
# aktuell in seeds/colors_en.json steht. Die begleitenden
# "is_covered_by"-Tests stellen sicher, dass ein künftiger
# Content-Import keinen Text stillschweigend ungeprüft lässt: Fehlt
# ein Text in dieser Tabelle (oder steht einer zu viel darin), schlägt
# der Abgleich fehl, statt einfach zu bestehen.

MEASURED_POLE_TEXT_WIDTHS = {
    "Chaos": 11.391,
    "Clear thinking": 25.523,
    "Codependency": 27.453,
    "Cold heartlessness": 34.906,
    "Complacency": 24.633,
    "Constraint": 19.047,
    "Destabilization": 27.195,
    "Emotion": 14.867,
    "Equilibrium": 20.500,
    "Evil": 6.492,
    "Exploitation": 21.656,
    "Flexibility": 17.547,
    "Freedom": 16.031,
    "Good": 9.742,
    "Group": 11.180,
    "Individual": 17.719,
    "Individualism": 24.039,
    "Leave it": 14.250,
    "Nature": 12.336,
    "Nurture": 14.094,
    "Optimization": 23.266,
    "Order": 10.516,
    "Pragmatism": 21.570,
    "Preservation": 23.086,
    "Reason": 13.336,
    "Short-sighted reacting": 41.727,
    "Structure": 17.188,
    "Take it": 11.992,
    "Warm aliveness": 28.477,
    "Waste": 11.203,
}
MEASURED_THEME_TEXT_WIDTHS = {
    "Authenticity": 27.242,
    "Community": 25.180,
    "Creativity": 21.789,
    "Design": 15.289,
    "Heroism": 18.430,
    "Independence": 31.359,
    "Profanity": 20.352,
    "Progress": 19.797,
    "Tribalism": 20.461,
    "Truth seeking": 30.438,
}

# Mindest-Sicherheitsabstand: die berechnete Box muss die real
# gemessene Textbreite um mindestens diesen Faktor überragen — ein
# knapp reichender Wert wäre in einer anderen Schriftart/Browser schon
# keiner mehr.
MIN_SAFETY_MARGIN = 1.10


@pytest.mark.usefixtures("seeded_content")
def test_every_pole_text_is_covered_by_the_measured_widths():
    """
    Schlägt fehl, sobald `seeds/colors_en.json` einen Pol-Text
    einführt oder entfernt, den MEASURED_POLE_TEXT_WIDTHS noch nicht
    kennt — macht eine Lücke sichtbar, statt sie stillschweigend
    ungeprüft zu lassen.
    """
    pole_terms = set(PerspectivePole.objects.values_list("term", flat=True))

    assert pole_terms == set(MEASURED_POLE_TEXT_WIDTHS)


@pytest.mark.usefixtures("seeded_content")
def test_every_theme_text_is_covered_by_the_measured_widths():
    theme_texts = set(
        ColorCombination.objects.exclude(theme="").values_list("theme", flat=True)
    )

    assert theme_texts == set(MEASURED_THEME_TEXT_WIDTHS)


@pytest.mark.parametrize("term,measured_width", sorted(MEASURED_POLE_TEXT_WIDTHS.items()))
def test_no_pole_label_text_is_wider_than_its_box(term, measured_width):
    box_width = pentagon._label_width(term, pentagon.POLE_LABEL_SIZE)

    assert box_width >= measured_width * MIN_SAFETY_MARGIN


@pytest.mark.parametrize("text,measured_width", sorted(MEASURED_THEME_TEXT_WIDTHS.items()))
def test_no_theme_label_text_is_wider_than_its_box(text, measured_width):
    box_width = pentagon._label_width(text, pentagon.THEME_LABEL_SIZE)

    assert box_width >= measured_width * MIN_SAFETY_MARGIN
