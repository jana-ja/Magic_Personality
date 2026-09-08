"""
Tests für das SVG-Layout des Fünfecks (Task 1.5, FR-C1 bis FR-C3).

Prüft die Geometrie, nicht das Aussehen: dass die Ecken dort liegen,
wo die Farbrad-Logik aus Task 1.2 sie hinrechnet, dass Reihenfolge und
Ausrichtung stimmen und dass nichts aus dem Bildausschnitt ragt.
"""

import pytest

from apps.colors import pentagon, wheel
from apps.colors.models import Color

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

    assert min_x == pytest.approx(-max_x)


def test_a_longer_color_name_widens_the_view_box(vertices):
    """
    Der Ausschnitt ist berechnet, nicht eingetragen — eine Übersetzung
    mit längeren Namen (D-15) darf nicht abgeschnitten werden.
    """
    before = _view_box(vertices)

    Color.objects.filter(code="U").update(name="Blue" * 5)
    after = _view_box(pentagon.vertices(Color.objects.all()))

    assert after[2] > before[2]
