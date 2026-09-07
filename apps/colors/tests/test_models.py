"""
Tests für die Content-Entitäten aus Task 1.1.

Der wichtigste Fall steht zuerst: die Datenmigration muss genau 31
Kombinationen anlegen, alle mit kanonisch sortiertem Code — das
verlangt die Definition of Done in docs/ROADMAP.md wörtlich.
"""

import pytest
from django.core.exceptions import ValidationError

from apps.colors.models import Color, ColorCombination, CombinationTrait, Perspective, Trait
from apps.colors.utils import canonical_code

pytestmark = pytest.mark.django_db


# Die Datenmigration (0002_seed_colors_and_combinations) -------------------


def test_exactly_31_combinations_exist_for_english():
    assert ColorCombination.objects.filter(locale="en").count() == 31


def test_every_combination_code_is_canonically_sorted():
    for combination in ColorCombination.objects.all():
        assert combination.code == canonical_code(combination.code)


def test_combination_sizes_cover_one_through_five_with_the_right_counts():
    """C(5,1)+C(5,2)+C(5,3)+C(5,4)+C(5,5) = 5+10+10+5+1 = 31."""
    counts = {size: 0 for size in range(1, 6)}
    for combination in ColorCombination.objects.all():
        counts[combination.size] += 1

    assert counts == {1: 5, 2: 10, 3: 10, 4: 5, 5: 1}


def test_all_combination_codes_are_unique_per_locale():
    codes = list(ColorCombination.objects.filter(locale="en").values_list("code", flat=True))
    assert len(codes) == len(set(codes))


def test_five_colors_exist_in_wheel_order_starting_with_white():
    colors = list(Color.objects.all())

    assert [color.code for color in colors] == ["W", "U", "B", "R", "G"]
    assert [color.wheel_position for color in colors] == [0, 1, 2, 3, 4]


# ColorCombination.clean() ---------------------------------------------------


def test_clean_rejects_a_non_canonically_sorted_code():
    combination = ColorCombination(code="UW", locale="en")

    with pytest.raises(ValidationError):
        combination.clean()


def test_clean_rejects_an_empty_code():
    combination = ColorCombination(code="", locale="en")

    with pytest.raises(ValidationError):
        combination.clean()


def test_clean_accepts_a_canonically_sorted_code():
    ColorCombination(code="WUB", locale="en").clean()  # raises nothing


# CombinationTrait.clean() ---------------------------------------------------


def test_leaning_toward_is_rejected_for_a_multi_color_combination():
    combination = ColorCombination.objects.get(code="WU", locale="en")
    trait = Trait.objects.create(name="Test Trait", type=Trait.TraitType.NEUTRAL, locale="en")

    combination_trait = CombinationTrait(
        combination=combination, trait=trait, leaning_toward=Color.Code.BLUE
    )

    with pytest.raises(ValidationError):
        combination_trait.clean()


def test_leaning_toward_is_accepted_for_an_actual_wheel_neighbor():
    """White (Position 0) und Blue (Position 1) sind Nachbarn (Azorius)."""
    combination = ColorCombination.objects.get(code="W", locale="en")
    trait = Trait.objects.create(name="Test Trait", type=Trait.TraitType.NEUTRAL, locale="en")

    combination_trait = CombinationTrait(
        combination=combination, trait=trait, leaning_toward=Color.Code.BLUE
    )

    combination_trait.clean()  # raises nothing


def test_leaning_toward_is_rejected_when_not_an_actual_wheel_neighbor():
    """White (Position 0) und Black (Position 2) sind Feinde, keine Nachbarn."""
    combination = ColorCombination.objects.get(code="W", locale="en")
    trait = Trait.objects.create(name="Test Trait", type=Trait.TraitType.NEUTRAL, locale="en")

    combination_trait = CombinationTrait(
        combination=combination, trait=trait, leaning_toward=Color.Code.BLACK
    )

    with pytest.raises(ValidationError):
        combination_trait.clean()


def test_combination_and_trait_must_share_the_same_locale():
    combination = ColorCombination.objects.get(code="W", locale="en")
    trait = Trait.objects.create(name="Testeigenschaft", type=Trait.TraitType.NEUTRAL, locale="de")

    with pytest.raises(ValidationError):
        CombinationTrait(combination=combination, trait=trait).clean()


# Perspective.clean() ---------------------------------------------------
# "WB" (White/Black) ist ein echtes Feindpaar (Orzhov) — siehe die
# relation-Tests weiter unten. "WU" (Azorius) ist bewusst *kein*
# Feindpaar und dient hier als Gegenprobe.


def test_perspective_requires_a_two_color_combination():
    combination = ColorCombination.objects.get(code="W", locale="en")

    with pytest.raises(ValidationError):
        Perspective(combination=combination, text="...", locale="en").clean()


def test_perspective_rejects_an_ally_pair():
    combination = ColorCombination.objects.get(code="WU", locale="en")

    with pytest.raises(ValidationError):
        Perspective(combination=combination, text="...", locale="en").clean()


def test_perspective_from_color_must_belong_to_the_combination():
    combination = ColorCombination.objects.get(code="WB", locale="en")

    with pytest.raises(ValidationError):
        Perspective(
            combination=combination, from_color=Color.Code.RED, text="...", locale="en"
        ).clean()


def test_perspective_locale_must_match_the_combination_locale():
    combination = ColorCombination.objects.get(code="WB", locale="en")

    with pytest.raises(ValidationError):
        Perspective(combination=combination, text="...", locale="de").clean()


def test_perspective_accepts_a_valid_enemy_pair_perspective():
    combination = ColorCombination.objects.get(code="WB", locale="en")

    Perspective(
        combination=combination, from_color=Color.Code.WHITE, text="...", locale="en"
    ).clean()  # raises nothing


def test_perspective_accepts_the_neutral_viewpoint():
    combination = ColorCombination.objects.get(code="WB", locale="en")

    Perspective(combination=combination, text="...", locale="en").clean()  # raises nothing


# ColorCombination.relation (Task 1.2, FR-C9, D-04) --------------------------
# Die zehn tatsächlichen Zweierkombinationen — fünf Ally- (die
# bekannten Gilden-Paare aus benachbarten Farben), fünf Enemy-Paare.

ALLY_PAIRS = ["WU", "WG", "UB", "BR", "RG"]
ENEMY_PAIRS = ["WB", "WR", "UR", "UG", "BG"]


@pytest.mark.parametrize("code", ALLY_PAIRS)
def test_relation_is_ally_for_the_five_real_ally_pairs(code):
    combination = ColorCombination.objects.get(code=code, locale="en")
    assert combination.relation == ColorCombination.Relation.ALLY


@pytest.mark.parametrize("code", ENEMY_PAIRS)
def test_relation_is_enemy_for_the_five_real_enemy_pairs(code):
    combination = ColorCombination.objects.get(code=code, locale="en")
    assert combination.relation == ColorCombination.Relation.ENEMY


def test_relation_is_none_for_a_single_color():
    combination = ColorCombination.objects.get(code="W", locale="en")
    assert combination.relation is None


def test_relation_is_none_for_three_or_more_colors():
    combination = ColorCombination.objects.get(code="WUB", locale="en")
    assert combination.relation is None


def test_all_ten_two_color_combinations_split_evenly_into_five_ally_five_enemy():
    two_color_combinations = [
        c for c in ColorCombination.objects.filter(locale="en") if c.size == 2
    ]
    assert len(two_color_combinations) == 10

    relations = [combination.relation for combination in two_color_combinations]
    assert relations.count(ColorCombination.Relation.ALLY) == 5
    assert relations.count(ColorCombination.Relation.ENEMY) == 5
