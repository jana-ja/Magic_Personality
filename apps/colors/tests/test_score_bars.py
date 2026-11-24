"""
Tests für den gemeinsamen Balken-Baustein (apps/colors/score_bars.py,
D-70, NFR-6). Wie die Balken im Profil und auf der Ergebnisseite
aussehen, prüfen die Seitentests in apps/social/tests/ und
apps/quiz/tests/; hier geht es um die Daten dahinter.
"""

import pytest

from apps.colors.score_bars import ordered_scores, score_bars

pytestmark = pytest.mark.django_db


def test_ordered_scores_follows_wubrg_regardless_of_the_dict_order():
    """PostgreSQL legt jsonb-Schlüssel als B, G, R, U, W ab — die Anzeige
    braucht trotzdem WUBRG."""
    scores = {"B": 3, "G": 5, "R": 0, "U": 2, "W": 1}

    assert ordered_scores(scores) == [("W", 1), ("U", 2), ("B", 3), ("R", 0), ("G", 5)]


def test_ordered_scores_fills_missing_colors_with_zero():
    assert ordered_scores({"U": 4}) == [("W", 0), ("U", 4), ("B", 0), ("R", 0), ("G", 0)]


def test_score_bars_are_relative_to_the_highest_score():
    bars = score_bars([("W", 2), ("U", 4), ("B", 0), ("R", 1), ("G", 3)])

    assert [bar["percent"] for bar in bars] == [50, 100, 0, 25, 75]
    assert [bar["points"] for bar in bars] == [2, 4, 0, 1, 3]


def test_score_bars_without_any_points_stay_empty_instead_of_dividing_by_zero():
    bars = score_bars(ordered_scores({}))

    assert [bar["percent"] for bar in bars] == [0] * 5
