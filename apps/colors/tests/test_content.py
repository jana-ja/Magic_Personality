"""
Tests für apps/colors/content.py (Task 1.7, PRD §5.2).

Prüft gegen die echte Seed-Datei (seeds/colors_en.json über die
Datenmigration + Task 1.4/1.6-Content), nicht gegen erfundene
Fixtures — die Geschäftslogik hier (welcher Nachbar ist "links",
welche Farbe ist der gemeinsame Feind) hat nur zusammen mit echten
Kombinationen eine überprüfbare Bedeutung.
"""

import pytest

from apps.colors.content import selection_content
from apps.colors.models import ColorCombination, Perspective

pytestmark = [pytest.mark.django_db, pytest.mark.usefixtures("seeded_content")]


# 0 Farben --------------------------------------------------------------


def test_zero_colors_has_goal_and_means_for_every_vertex():
    content = selection_content(set())

    assert set(content["vertex_extra"]) == set("WUBRG")
    for code, (goal, means) in content["vertex_extra"].items():
        assert goal and means, code


def test_zero_colors_labels_all_five_ally_edges_and_enemy_diagonals():
    content = selection_content(set())

    assert {pair for pair, _ in content["theme_labels"]} == {"WU", "UB", "BR", "RG", "WG"}
    assert {pair for pair, _, _ in content["pole_labels"]} == {"WB", "WR", "UR", "UG", "BG"}
    # Neutrale Sicht: zwei Pole je Diagonale.
    assert len(content["pole_labels"]) == 10


def test_zero_colors_box_is_the_reserved_placeholder():
    content = selection_content(set())

    assert content["box"] == {"kind": "none"}
    assert content["trait_groups"] is None


# 1 Farbe -----------------------------------------------------------------


def test_one_color_box_has_name_question_allies_and_enemies():
    content = selection_content({"W"})

    assert content["box"] == {
        "kind": "single",
        "name": "White",
        "guiding_question": ColorCombination.objects.get(code="W", locale="en").guiding_question,
        "allies": ["Green", "Blue"],
        "enemies": ["Black", "Red"],
    }


def test_one_color_traits_split_into_center_and_both_neighbors():
    content = selection_content({"W"})
    groups = content["trait_groups"]

    assert groups["kind"] == "single"
    assert groups["left_name"] == "Green"
    assert groups["right_name"] == "Blue"
    assert len(groups["center"]) == 6
    assert len(groups["left"]) == 2
    assert len(groups["right"]) == 2


def test_one_color_pentagon_shows_its_own_ally_edges_and_own_view_of_enemies():
    content = selection_content({"W"})

    assert {pair for pair, _ in content["theme_labels"]} == {"WU", "WG"}
    assert {pair for pair, _, _ in content["pole_labels"]} == {"WB", "WR"}
    # Eigene Sicht, nicht die neutrale — "Good"/"Order" statt "Group"/"Structure".
    terms = {term for _, _, term in content["pole_labels"]}
    assert terms == {"Good", "Evil", "Order", "Chaos"}


def test_one_color_vertex_extra_is_empty_once_selected():
    content = selection_content({"W"})

    assert content["vertex_extra"] == {}


# 2 Farben, Ally ------------------------------------------------------------


def test_ally_pair_box_has_relation_name_archetype_and_the_new_fields():
    content = selection_content({"W", "U"})

    assert content["box"] == {
        "kind": "ally",
        "relation_label": "Ally",
        "name": "Azorius",
        "archetype": "The Architect",
        "guiding_question": ColorCombination.objects.get(code="WU", locale="en").guiding_question,
        "common_enemy": "Red",
        "conflict_text": "Take it vs Leave it",
    }


def test_ally_pair_traits_are_a_single_unsplit_group():
    content = selection_content({"W", "U"})
    groups = content["trait_groups"]

    assert groups == {
        "kind": "one-box",
        "title": "Azorius",
        "traits": groups["traits"],  # Inhalt separat geprüft
    }
    assert {t["name"] for t in groups["traits"]} == {
        "Design Mindset",
        "Procedural Fairness",
        "Bureaucratic Drift",
    }


def test_ally_pair_pentagon_shows_three_edges_and_three_diagonals():
    content = selection_content({"W", "U"})

    assert {pair for pair, _ in content["theme_labels"]} == {"WU", "WG", "UB"}
    assert {pair for pair, _, _ in content["pole_labels"]} == {"WR", "UR", "BG"}
    # WR/UR: eigene Sicht der beiden selektierten Farben auf den
    # gemeinsamen Feind. BG: neutrale Sicht auf die übrigen Nachbarn.
    by_pair = {}
    for pair, color, term in content["pole_labels"]:
        by_pair.setdefault(pair, {})[color] = term
    assert by_pair["WR"] == {"W": "Order", "R": "Chaos"}
    assert by_pair["UR"] == {"U": "Clear thinking", "R": "Short-sighted reacting"}
    assert by_pair["BG"] == {"B": "Take it", "G": "Leave it"}


@pytest.mark.parametrize(
    "pair,common_enemy,conflict",
    [
        ({"W", "U"}, "Red", "Take it vs Leave it"),
        ({"W", "G"}, "Black", "Reason vs Emotion"),
        ({"U", "B"}, "Green", "Structure vs Flexibility"),
        ({"B", "R"}, "White", "Nurture vs Nature"),
        ({"R", "G"}, "Blue", "Group vs Individual"),
    ],
)
def test_common_enemy_and_conflict_for_every_ally_pair(pair, common_enemy, conflict):
    content = selection_content(pair)

    assert content["box"]["common_enemy"] == common_enemy
    assert content["box"]["conflict_text"] == conflict


# 2 Farben, Enemy -------------------------------------------------------


def test_enemy_pair_box_has_all_three_perspectives_in_a_fixed_order():
    content = selection_content({"W", "B"})
    box = content["box"]

    assert box["kind"] == "enemy"
    assert box["relation_label"] == "Enemy"
    assert box["name"] == "Orzhov"
    assert box["archetype"] == "The Insider"
    viewpoints = [p["from_color"] for p in box["perspectives"]]
    assert viewpoints == ["W", "B", ""]
    assert box["perspectives"][0]["from_name"] == "White"
    assert box["perspectives"][2]["from_name"] is None

    assert content["trait_groups"] is None


def test_perspective_order_does_not_depend_on_row_insertion_order():
    """
    Perspective hat kein Meta.ordering — die Reihenfolge, in der die
    Datenbank Zeilen zurückgibt, ist ohne ORDER BY nicht garantiert.
    Der Seed-Datei nach entstehen die drei Zeilen zufällig schon in
    Anzeigereihenfolge (W, B, neutral), weshalb der Test oben eine
    falsche Sortierung nicht zuverlässig aufdecken würde. Hier werden
    dieselben drei Zeilen absichtlich in umgekehrter Reihenfolge neu
    angelegt, um die explizite Sortierung in content.py tatsächlich
    zu prüfen.
    """
    combination = ColorCombination.objects.get(code="WB", locale="en")
    combination.perspectives.all().delete()
    for from_color, text in [("", "Neutral text."), ("B", "Black's text."), ("W", "White's text.")]:
        Perspective.objects.create(combination=combination, from_color=from_color, text=text)

    content = selection_content({"W", "B"})

    viewpoints = [p["from_color"] for p in content["box"]["perspectives"]]
    assert viewpoints == ["W", "B", ""]


def test_enemy_pair_pentagon_shows_only_its_own_diagonal_with_theme_and_neutral_poles():
    content = selection_content({"W", "B"})

    assert content["theme_labels"] == [("WB", "Tribalism")]
    assert {(color, term) for _, color, term in content["pole_labels"]} == {
        ("W", "Group"),
        ("B", "Individual"),
    }


# 3-5 Farben ------------------------------------------------------------


@pytest.mark.parametrize(
    "selected,expected_name",
    [({"W", "U", "B"}, "Esper"), ({"W", "U", "B", "R", "G"}, "WUBRG")],
)
def test_larger_combinations_show_only_the_name(selected, expected_name):
    content = selection_content(selected)

    assert content["box"] == {"kind": "many", "name": expected_name}
    assert content["theme_labels"] == []
    assert content["pole_labels"] == []
    assert content["trait_groups"] is None


def test_a_combination_without_content_renders_an_empty_name_not_an_error():
    """Roadmap 1.7: 'eine 3er-Kombination ohne Content rendert fehlerfrei' (FR-C11)."""
    ColorCombination.objects.filter(code="WUB", locale="en").update(name="")

    content = selection_content({"W", "U", "B"})

    assert content["box"] == {"kind": "many", "name": ""}
