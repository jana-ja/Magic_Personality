"""
Tests für die ausgelieferte Content-Datei seeds/colors_en.json
(Task 1.4, PRD §9, D-12).

Anders als test_seed_content.py, das die *Mechanik* gegen eigene
Fixtures prüft, geht es hier um den *Inhalt*: Die Datei wird wie im
Betrieb eingespielt und anschließend gegen die Anzeige-Tabelle aus
PRD §5.2 geprüft — das, was Task 1.7 später rendern muss, ist damit
auch tatsächlich vorhanden.
"""

import itertools

import pytest
from django.conf import settings
from django.core.management import call_command

from apps.colors.models import ColorCombination, Perspective, PerspectivePole, Trait
from apps.colors.utils import CANONICAL_ORDER

pytestmark = pytest.mark.django_db

SEED_PATH = settings.BASE_DIR / "seeds" / "colors_en.json"

ALL_CODES = {
    "".join(combination)
    for size in range(1, 6)
    for combination in itertools.combinations(CANONICAL_ORDER, size)
}


@pytest.fixture
def seeded():
    """Spielt die echte Datei ein und liefert {code: ColorCombination}."""
    call_command("seed_content", locale="en", path=str(SEED_PATH))
    return {
        combination.code: combination
        for combination in ColorCombination.objects.filter(locale="en")
    }


def test_the_shipped_file_seeds_all_31_combinations(seeded):
    assert set(seeded) == ALL_CODES


def test_every_combination_has_a_name(seeded):
    assert [code for code, combination in seeded.items() if not combination.name] == []


# Einzelfarben (PRD §5.2, Zeile "1 Farbe") ----------------------------------


def test_single_colors_carry_goal_means_and_guiding_question(seeded):
    incomplete = {
        code: [
            field
            for field in ("goal", "means", "guiding_question")
            if not getattr(seeded[code], field)
        ]
        for code in CANONICAL_ORDER
    }
    assert {code: missing for code, missing in incomplete.items() if missing} == {}


def test_single_colors_have_traits_at_the_center_and_toward_both_neighbors(seeded):
    # "" ist center; dazu genau die beiden Rad-Nachbarn. *Welche* das
    # sind, prüft bereits CombinationTrait.clean() beim Import — hier
    # geht es nur darum, dass beide Richtungen überhaupt befüllt sind.
    leanings = {
        code: {link.leaning_toward for link in seeded[code].combination_traits.all()}
        for code in CANONICAL_ORDER
    }
    assert {code: sorted(found) for code, found in leanings.items() if "" not in found} == {}
    assert {code: sorted(found) for code, found in leanings.items() if len(found - {""}) != 2} == {}


# Zweierkombinationen (PRD §5.2, Zeile "2 Farben") --------------------------


def _codes_of_size(size):
    return sorted("".join(pair) for pair in itertools.combinations(CANONICAL_ORDER, size))


def test_two_color_combinations_carry_guiding_question_and_archetype(seeded):
    incomplete = {
        code: [
            field for field in ("guiding_question", "archetype") if not getattr(seeded[code], field)
        ]
        for code in _codes_of_size(2)
    }
    assert {code: missing for code, missing in incomplete.items() if missing} == {}


def test_ally_pairs_have_traits(seeded):
    ally_codes = [
        code
        for code in _codes_of_size(2)
        if seeded[code].relation == ColorCombination.Relation.ALLY
    ]
    assert len(ally_codes) == 5

    assert [code for code in ally_codes if not seeded[code].combination_traits.exists()] == []
    assert [code for code in ally_codes if seeded[code].perspectives.exists()] == []


def test_enemy_pairs_have_all_three_perspectives(seeded):
    enemy_codes = [
        code
        for code in _codes_of_size(2)
        if seeded[code].relation == ColorCombination.Relation.ENEMY
    ]
    assert len(enemy_codes) == 5

    # Beide eigenen Farben plus die neutrale Sicht ("" = leer).
    viewpoints = {
        code: {perspective.from_color for perspective in seeded[code].perspectives.all()}
        for code in enemy_codes
    }
    assert viewpoints == {code: {code[0], code[1], ""} for code in enemy_codes}
    assert [code for code in enemy_codes if seeded[code].combination_traits.exists()] == []


def test_two_color_combinations_carry_a_theme(seeded):
    """Das Wort auf der Linie zwischen zwei Farben im Fünfeck (D-37)."""
    assert [code for code in _codes_of_size(2) if not seeded[code].theme] == []


def test_every_perspective_has_one_pole_per_color_of_its_pair(seeded):
    """
    Je Perspektive genau zwei Wörter, eines an jedem Ende der
    Diagonale — auch bei der neutralen Sicht (D-37).
    """
    found = {}
    for code in _codes_of_size(2):
        for perspective in seeded[code].perspectives.all():
            key = (code, perspective.from_color or "neutral")
            found[key] = {pole.color for pole in perspective.poles.all()}

    assert found == {key: {key[0][0], key[0][1]} for key in found}
    assert len(found) == 15


# Fünfeck-Beschriftung im Default-Zustand -----------------------------------


def test_the_unselected_pentagon_matches_the_reference_drawing(seeded):
    """
    Der Zustand ohne Selektion ist die Ansicht, die jede*r zuerst
    sieht — die Wörter sind hier fest an docs/reference/
    default_0_selected.png gepinnt, damit sie nicht unbemerkt
    verrutschen. Die übrigen Zustände prüfen nur ihre Struktur.
    """
    ally_themes = {
        code: seeded[code].theme
        for code in _codes_of_size(2)
        if seeded[code].relation == ColorCombination.Relation.ALLY
    }
    assert ally_themes == {
        "WU": "Design",
        "WG": "Community",
        "UB": "Progress",
        "BR": "Independence",
        "RG": "Authenticity",
    }

    neutral_poles = {}
    for code in _codes_of_size(2):
        if seeded[code].relation != ColorCombination.Relation.ENEMY:
            continue
        perspective = seeded[code].perspectives.get(from_color="")
        neutral_poles[code] = {pole.color: pole.term for pole in perspective.poles.all()}

    assert neutral_poles == {
        "WB": {"W": "Group", "B": "Individual"},
        "WR": {"W": "Structure", "R": "Flexibility"},
        "UR": {"U": "Reason", "R": "Emotion"},
        "UG": {"U": "Nurture", "G": "Nature"},
        "BG": {"B": "Take it", "G": "Leave it"},
    }


def test_goal_and_means_fit_next_to_a_pentagon_corner(seeded):
    """
    An der Ecke steht "peace" / "through order", kein ganzer Satz —
    die Kurzform ist hier die erfasste Fassung (D-37).
    """
    too_long = {
        code: (seeded[code].goal, seeded[code].means)
        for code in CANONICAL_ORDER
        if len(seeded[code].goal.split()) > 1 or len(seeded[code].means.split()) > 1
    }
    assert too_long == {}


# Drei bis fünf Farben (FR-C11, D-02) --------------------------------------


def test_larger_combinations_carry_the_name_and_nothing_else(seeded):
    larger = sorted(code for code in ALL_CODES if len(code) >= 3)
    assert len(larger) == 16

    filled = {}
    for code in larger:
        combination = seeded[code]
        extra = [
            field
            for field in ("goal", "means", "guiding_question", "archetype", "theme")
            if getattr(combination, field)
        ]
        if combination.combination_traits.exists():
            extra.append("traits")
        if combination.perspectives.exists():
            extra.append("perspectives")
        if extra:
            filled[code] = extra
    assert filled == {}


# Struktur der Datei selbst -------------------------------------------------


def test_trait_names_are_unique_across_the_whole_file(seeded):
    """
    (name, locale) ist der natürliche Schlüssel (D-33): ein doppelt
    vergebener Name wäre eine geteilte Zeile, deren zweite Nennung die
    erste überschreibt. Solange das nicht ausdrücklich gewollt ist,
    hält dieser Test es fest (D-36).
    """
    links = sum(combination.combination_traits.count() for combination in seeded.values())
    assert links == Trait.objects.filter(locale="en").count()


def test_seeding_the_shipped_file_twice_changes_nothing(seeded):
    before = (
        sorted(ColorCombination.objects.values_list("code", "name", "guiding_question")),
        sorted(Trait.objects.values_list("name", "description", "type")),
        sorted(Perspective.objects.values_list("combination__code", "from_color", "text")),
        sorted(
            PerspectivePole.objects.values_list("perspective__combination__code", "color", "term")
        ),
    )

    call_command("seed_content", locale="en", path=str(SEED_PATH))

    after = (
        sorted(ColorCombination.objects.values_list("code", "name", "guiding_question")),
        sorted(Trait.objects.values_list("name", "description", "type")),
        sorted(Perspective.objects.values_list("combination__code", "from_color", "text")),
        sorted(
            PerspectivePole.objects.values_list("perspective__combination__code", "color", "term")
        ),
    )
    assert before == after
