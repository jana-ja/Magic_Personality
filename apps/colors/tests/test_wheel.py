"""
Tests für die reine Geometrie-/Beziehungslogik (Task 1.2).

Arbeitet bewusst mit reinen Positionen (0..4), nicht mit der
Datenbank — apps/colors/tests/test_models.py prüft die Brücke zu
echten Farbcodes über ColorCombination.relation.
"""

import math

import pytest

from apps.colors import wheel

ADJACENT_PAIRS = [(0, 1), (1, 2), (2, 3), (3, 4), (4, 0)]
NON_ADJACENT_PAIRS = [(0, 2), (0, 3), (1, 3), (1, 4), (2, 4)]


@pytest.mark.parametrize("position_a,position_b", ADJACENT_PAIRS)
def test_are_neighbors_true_for_adjacent_positions(position_a, position_b):
    assert wheel.are_neighbors(position_a, position_b) is True


@pytest.mark.parametrize("position_a,position_b", NON_ADJACENT_PAIRS)
def test_are_neighbors_false_for_non_adjacent_positions(position_a, position_b):
    assert wheel.are_neighbors(position_a, position_b) is False


def test_are_neighbors_false_for_the_same_position():
    assert wheel.are_neighbors(2, 2) is False


@pytest.mark.parametrize("position_a,position_b", NON_ADJACENT_PAIRS)
def test_are_enemies_true_for_non_adjacent_positions(position_a, position_b):
    assert wheel.are_enemies(position_a, position_b) is True


@pytest.mark.parametrize("position_a,position_b", ADJACENT_PAIRS)
def test_are_enemies_false_for_adjacent_positions(position_a, position_b):
    assert wheel.are_enemies(position_a, position_b) is False


def test_are_enemies_false_for_the_same_position():
    assert wheel.are_enemies(2, 2) is False


def test_every_pair_is_either_neighbor_or_enemy_never_both():
    for position_a in range(wheel.POSITION_COUNT):
        for position_b in range(wheel.POSITION_COUNT):
            if position_a == position_b:
                assert not wheel.are_neighbors(position_a, position_b)
                assert not wheel.are_enemies(position_a, position_b)
            else:
                assert wheel.are_neighbors(position_a, position_b) != wheel.are_enemies(
                    position_a, position_b
                )


def test_wheel_coordinates_places_position_zero_at_the_top():
    x, y = wheel.wheel_coordinates(0)

    assert x == pytest.approx(0, abs=1e-9)
    assert y < 0  # negatives y = oben, in SVG-Koordinaten.


def test_wheel_coordinates_go_clockwise():
    """Position 1 muss rechts der Mitte liegen (FR-C1: 'dann rechtsrum blau')."""
    x, _y = wheel.wheel_coordinates(1)

    assert x > 0


def test_wheel_coordinates_are_evenly_spaced_on_the_circle():
    center = (0.0, 0.0)
    radius = 2.0

    for position in range(wheel.POSITION_COUNT):
        x, y = wheel.wheel_coordinates(position, radius=radius, center=center)
        assert math.hypot(x - center[0], y - center[1]) == pytest.approx(radius)


def test_wheel_coordinates_respect_a_custom_center():
    x, y = wheel.wheel_coordinates(0, radius=1.0, center=(5.0, 5.0))

    assert x == pytest.approx(5.0, abs=1e-9)
    assert y == pytest.approx(4.0)  # eine Einheit "über" der Mitte.
