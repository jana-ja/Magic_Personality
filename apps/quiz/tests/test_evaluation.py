"""
Tests für die Auswertungsregel (Task 2.9, FR-T10 bis FR-T12, D-17).

Die fünf Fälle aus der Definition of Done in docs/ROADMAP.md stehen
hier wörtlich als eigene Tests: klarer Dreier, deutlicher Zweier,
deutlicher Vierer, Gleichstand an der Grenze, Gleichstand über alle
fünf.
"""

import pytest

from apps.colors.models import ColorCombination
from apps.quiz.evaluation import evaluate, evaluate_combination, result_size

pytestmark = pytest.mark.django_db


def _scores(w, u, b, r, g):
    return {"W": w, "U": u, "B": b, "R": r, "G": g}


# Die fünf Fälle aus der Definition of Done -------------------------------


def test_a_clear_three_stays_at_the_default():
    """G(2)=2, G(3)=3, G(4)=0 — kein Abstand überschreitet G(3)+T."""
    scores = _scores(8, 6, 4, 1, 1)

    assert evaluate(scores, threshold=2) == {"W", "U", "B"}


def test_a_clear_two_narrows_the_result():
    """G(2)=6 >= G(3)+T (2+2) -> k=2."""
    scores = _scores(10, 8, 2, 0, 0)

    assert evaluate(scores, threshold=2) == {"W", "U"}


def test_a_clear_four_widens_the_result():
    """G(4)=3 >= G(3)+T (1+2) -> k=4."""
    scores = _scores(6, 5, 4, 3, 0)

    assert evaluate(scores, threshold=2) == {"W", "U", "B", "R"}


def test_a_tie_at_the_cutoff_pulls_in_the_tied_color():
    """Kein Übersteuern (k bleibt 3), aber Rang 3 und 4 sind
    punktgleich (6 = 6) -> beide kommen ins Ergebnis (FR-T12)."""
    scores = _scores(8, 7, 6, 6, 5)

    assert evaluate(scores, threshold=2) == {"W", "U", "B", "R"}


def test_a_five_way_tie_results_in_all_five_colors():
    scores = _scores(4, 4, 4, 4, 4)

    assert evaluate(scores, threshold=2) == {"W", "U", "B", "R", "G"}


# Weitere Randfälle --------------------------------------------------------


def test_threshold_is_configurable():
    """Mit einem kleineren T wird derselbe Punktestand zum deutlichen
    Zweier statt zum Standard-Dreier: G(2)=3, G(3)=2 — bei T=2 reicht
    der Abstand nicht (3 < 2+2), bei T=1 schon (3 >= 2+1)."""
    scores = _scores(9, 8, 5, 3, 2)

    assert evaluate(scores, threshold=2) == {"W", "U", "B"}
    assert evaluate(scores, threshold=1) == {"W", "U"}


def test_threshold_has_no_global_default():
    """D-65: `T` gehört zur Punkteskala einer Fragebogen-Version und
    muss deshalb immer ausdrücklich übergeben werden."""
    with pytest.raises(TypeError):
        evaluate(_scores(10, 8, 2, 0, 0))


def test_a_tie_between_both_overrides_falls_back_to_the_default():
    """G(2) und G(4) übersteuern beide auf ihre Weise, sind aber
    gleich groß — die PRD nennt dafür keinen Sieger (FR-T11.4), also
    bleibt es beim Standard."""
    scores = _scores(6, 5, 4, 3, 2)  # G(2)=1, G(3)=1, G(4)=1

    # Beide Bedingungen (G(2)>=G(3)+T, G(4)>=G(3)+T) mit T=0 erfüllt
    # und exakt gleich groß.
    assert evaluate(scores, threshold=0) == {"W", "U", "B"}


def test_result_size_matches_evaluate_before_tie_extension():
    assert result_size([8, 6, 4, 1, 1], threshold=2) == 3
    assert result_size([10, 8, 2, 0, 0], threshold=2) == 2
    assert result_size([6, 5, 4, 3, 0], threshold=2) == 4


# Abbildung auf eine der 31 Kombinationen ----------------------------------


def test_evaluate_combination_maps_to_a_real_combination():
    scores = _scores(8, 6, 4, 1, 1)

    combination = evaluate_combination(scores, threshold=2)

    assert combination == ColorCombination.objects.get(code="WUB", locale="en")


def test_evaluate_combination_handles_a_two_color_result():
    scores = _scores(10, 8, 2, 0, 0)

    combination = evaluate_combination(scores, threshold=2)

    assert combination.code == "WU"


def test_evaluate_combination_handles_a_five_way_tie():
    scores = _scores(4, 4, 4, 4, 4)

    combination = evaluate_combination(scores, threshold=2)

    assert combination.code == "WUBRG"
