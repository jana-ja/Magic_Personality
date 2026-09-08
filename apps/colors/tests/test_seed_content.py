"""
Tests für `manage.py seed_content` (Task 1.3, D-28).

Nutzt ausschließlich eigene, kleine Test-Fixtures über --path — nie
die echte seeds/colors_en.json, die sich unabhängig von diesen Tests
ändert. Deren *Inhalt* prüft test_seed_file_en.py (Task 1.4).
"""

import json

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from apps.colors.models import (
    ColorCombination,
    CombinationTrait,
    Perspective,
    PerspectivePole,
    Trait,
)

pytestmark = pytest.mark.django_db


def _seed(tmp_path, data, *, locale="en", filename="seed.json"):
    path = tmp_path / filename
    path.write_text(json.dumps(data), encoding="utf-8")
    call_command("seed_content", locale=locale, path=str(path))
    return path


def _seed_raises(tmp_path, data, *, locale="en"):
    path = tmp_path / "seed.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(CommandError) as excinfo:
        call_command("seed_content", locale=locale, path=str(path))
    return str(excinfo.value)


# Grundlegende Fehlerfälle ---------------------------------------------------


def test_missing_locale_argument_raises():
    with pytest.raises(CommandError):
        call_command("seed_content")


def test_missing_file_raises_a_clear_error(tmp_path):
    missing = tmp_path / "does-not-exist.json"
    with pytest.raises(CommandError, match="nicht gefunden"):
        call_command("seed_content", locale="en", path=str(missing))


def test_invalid_json_raises_a_clear_error(tmp_path):
    path = tmp_path / "broken.json"
    path.write_text("{not valid json", encoding="utf-8")

    with pytest.raises(CommandError, match="kein gültiges JSON"):
        call_command("seed_content", locale="en", path=str(path))


def test_locale_mismatch_between_argument_and_file_raises(tmp_path):
    message = _seed_raises(tmp_path, {"locale": "de", "combinations": []}, locale="en")
    assert "de" in message and "en" in message


# Unbekannte Felder ("Tippfehler brechen ab") --------------------------------


def test_unknown_top_level_field_raises(tmp_path):
    message = _seed_raises(tmp_path, {"locale": "en", "combinations": [], "extra": 1})
    assert "extra" in message


def test_unknown_combination_field_raises(tmp_path):
    data = {"locale": "en", "combinations": [{"code": "W", "typo_field": "x"}]}
    message = _seed_raises(tmp_path, data)
    assert "typo_field" in message


def test_unknown_trait_field_raises(tmp_path):
    data = {
        "locale": "en",
        "combinations": [
            {"code": "W", "traits": [{"name": "X", "type": "NEUTRAL", "not_a_field": 1}]}
        ],
    }
    message = _seed_raises(tmp_path, data)
    assert "not_a_field" in message


def test_unknown_perspective_field_raises(tmp_path):
    data = {
        "locale": "en",
        "combinations": [{"code": "WB", "perspectives": [{"text": "...", "bogus": 1}]}],
    }
    message = _seed_raises(tmp_path, data)
    assert "bogus" in message


# Unbekannte Farbcodes ---------------------------------------------------


@pytest.mark.parametrize("bad_code", ["UW", "X", "WUBRGW"])
def test_invalid_color_code_raises(tmp_path, bad_code):
    data = {"locale": "en", "combinations": [{"code": bad_code}]}
    message = _seed_raises(tmp_path, data)
    assert "Farbcode" in message


def test_missing_code_raises_a_dedicated_error(tmp_path):
    data = {"locale": "en", "combinations": [{"name": "no code here"}]}
    message = _seed_raises(tmp_path, data)
    assert "code" in message


# Erfolgreicher Import ---------------------------------------------------


def test_seed_creates_a_combination_with_content(tmp_path):
    data = {
        "locale": "en",
        "combinations": [
            {
                "code": "W",
                "name": "White",
                "goal": "Peace",
                "means": "Order",
                "guiding_question": "What is right?",
                "traits": [
                    {
                        "name": "Compassion",
                        "description": "Caring for others.",
                        "type": "STRENGTH",
                        "leaning_toward": None,
                    },
                    {
                        "name": "Self-righteousness",
                        "description": "Certainty of one's own rules.",
                        "type": "WEAKNESS",
                        "leaning_toward": "U",
                    },
                ],
            }
        ],
    }

    _seed(tmp_path, data)

    combination = ColorCombination.objects.get(code="W", locale="en")
    assert combination.name == "White"
    assert combination.goal == "Peace"

    traits = {t.trait.name: t for t in combination.combination_traits.select_related("trait")}
    assert traits["Compassion"].leaning_toward == ""
    assert traits["Self-righteousness"].leaning_toward == "U"
    assert Trait.objects.get(name="Compassion").type == Trait.TraitType.STRENGTH


def test_seed_creates_all_three_perspectives_for_an_enemy_pair(tmp_path):
    data = {
        "locale": "en",
        "combinations": [
            {
                "code": "WB",
                "name": "Orzhov",
                "perspectives": [
                    {"from_color": "W", "text": "White's view"},
                    {"from_color": "B", "text": "Black's view"},
                    {"from_color": None, "text": "Neutral view"},
                ],
            }
        ],
    }

    _seed(tmp_path, data)

    combination = ColorCombination.objects.get(code="WB", locale="en")
    perspectives = {p.from_color: p.text for p in combination.perspectives.all()}
    assert perspectives == {
        "W": "White's view",
        "B": "Black's view",
        "": "Neutral view",
    }


def test_seed_creates_the_poles_of_a_perspective(tmp_path):
    """Die zwei Wörter je Perspektive, jedes an seine Farbe gebunden (D-37)."""
    data = {
        "locale": "en",
        "combinations": [
            {
                "code": "WB",
                "perspectives": [
                    {
                        "from_color": "W",
                        "text": "White's view",
                        "poles": [
                            {"color": "W", "term": "Good"},
                            {"color": "B", "term": "Evil"},
                        ],
                    },
                    {
                        "from_color": None,
                        "text": "Neutral view",
                        "poles": [
                            {"color": "W", "term": "Group"},
                            {"color": "B", "term": "Individual"},
                        ],
                    },
                ],
            }
        ],
    }

    _seed(tmp_path, data)

    combination = ColorCombination.objects.get(code="WB", locale="en")
    by_viewpoint = {
        perspective.from_color: {pole.color: pole.term for pole in perspective.poles.all()}
        for perspective in combination.perspectives.all()
    }
    assert by_viewpoint == {
        "W": {"W": "Good", "B": "Evil"},
        "": {"W": "Group", "B": "Individual"},
    }


def test_seed_rejects_a_pole_for_a_color_outside_the_pair(tmp_path):
    message = _seed_raises(
        tmp_path,
        {
            "locale": "en",
            "combinations": [
                {
                    "code": "WB",
                    "perspectives": [
                        {
                            "from_color": "W",
                            "text": "...",
                            "poles": [{"color": "R", "term": "Chaos"}],
                        }
                    ],
                }
            ],
        },
    )
    assert "color" in message


def test_unknown_pole_field_raises(tmp_path):
    message = _seed_raises(
        tmp_path,
        {
            "locale": "en",
            "combinations": [
                {
                    "code": "WB",
                    "perspectives": [
                        {
                            "from_color": "W",
                            "text": "...",
                            "poles": [{"color": "W", "term": "Good", "labl": "typo"}],
                        }
                    ],
                }
            ],
        },
    )
    assert "labl" in message


def test_a_pole_without_color_or_term_raises(tmp_path):
    message = _seed_raises(
        tmp_path,
        {
            "locale": "en",
            "combinations": [
                {
                    "code": "WB",
                    "perspectives": [{"from_color": "W", "text": "...", "poles": [{"color": "W"}]}],
                }
            ],
        },
    )
    assert "term" in message


def test_seeding_poles_twice_updates_in_place(tmp_path):
    data = {
        "locale": "en",
        "combinations": [
            {
                "code": "WB",
                "perspectives": [
                    {
                        "from_color": "W",
                        "text": "...",
                        "poles": [{"color": "W", "term": "Good"}],
                    }
                ],
            }
        ],
    }
    _seed(tmp_path, data)

    data["combinations"][0]["perspectives"][0]["poles"][0]["term"] = "Order"
    _seed(tmp_path, data)

    assert [(pole.color, pole.term) for pole in PerspectivePole.objects.all()] == [("W", "Order")]


def test_seed_stores_the_theme_of_a_combination(tmp_path):
    _seed(
        tmp_path,
        {
            "locale": "en",
            "combinations": [
                {"code": "WU", "name": "Azorius", "theme": "Design"},
                {"code": "WB", "name": "Orzhov", "theme": "Tribalism"},
            ],
        },
    )

    themes = dict(
        ColorCombination.objects.filter(code__in=["WU", "WB"], locale="en").values_list(
            "code", "theme"
        )
    )
    assert themes == {"WU": "Design", "WB": "Tribalism"}


def test_seed_rejects_a_perspective_on_an_ally_pair(tmp_path):
    data = {
        "locale": "en",
        "combinations": [{"code": "WU", "perspectives": [{"text": "Should not be allowed"}]}],
    }

    message = _seed_raises(tmp_path, data)
    assert "WU" in message


def test_seed_rejects_leaning_toward_that_is_not_a_wheel_neighbor(tmp_path):
    data = {
        "locale": "en",
        "combinations": [
            {"code": "W", "traits": [{"name": "X", "type": "NEUTRAL", "leaning_toward": "B"}]}
        ],
    }

    _seed_raises(tmp_path, data)


# Idempotenz (Definition of Done) --------------------------------------


def test_running_the_same_seed_twice_changes_nothing(tmp_path):
    data = {
        "locale": "en",
        "combinations": [
            {
                "code": "WB",
                "name": "Orzhov",
                "archetype": "The Aristocrat",
                "perspectives": [
                    {"from_color": "W", "text": "White's view"},
                    {"from_color": "B", "text": "Black's view"},
                    {"from_color": None, "text": "Neutral view"},
                ],
            }
        ],
    }

    _seed(tmp_path, data, filename="first.json")
    combination_id = ColorCombination.objects.get(code="WB", locale="en").id
    perspective_ids = set(Perspective.objects.values_list("id", flat=True))
    combination_count = ColorCombination.objects.count()

    _seed(tmp_path, data, filename="second.json")

    assert ColorCombination.objects.count() == combination_count
    assert ColorCombination.objects.get(code="WB", locale="en").id == combination_id
    assert set(Perspective.objects.values_list("id", flat=True)) == perspective_ids


def test_running_the_seed_again_with_changed_content_updates_in_place(tmp_path):
    first = {"locale": "en", "combinations": [{"code": "W", "name": "White", "goal": "Peace"}]}
    _seed(tmp_path, first, filename="first.json")
    combination_id = ColorCombination.objects.get(code="W", locale="en").id

    second = {"locale": "en", "combinations": [{"code": "W", "name": "White", "goal": "Order"}]}
    _seed(tmp_path, second, filename="second.json")

    combination = ColorCombination.objects.get(code="W", locale="en")
    assert combination.id == combination_id
    assert combination.goal == "Order"
    assert ColorCombination.objects.filter(code="W", locale="en").count() == 1


def test_a_failed_seed_rolls_back_everything_from_that_run(tmp_path):
    """
    Die zweite Kombination im selben Lauf ist ungültig — die erste,
    an sich gültige, darf trotzdem nicht übrig bleiben (eine
    Transaktion für den gesamten Lauf, siehe seeds/README.md).
    """
    data = {
        "locale": "en",
        "combinations": [
            {"code": "G", "name": "Green"},
            {"code": "INVALID"},
        ],
    }

    with pytest.raises(CommandError):
        _seed(tmp_path, data)

    assert not ColorCombination.objects.filter(code="G", locale="en", name="Green").exists()


def test_seeding_does_not_create_a_combination_trait_link_twice(tmp_path):
    data = {
        "locale": "en",
        "combinations": [{"code": "W", "traits": [{"name": "Compassion", "type": "STRENGTH"}]}],
    }

    _seed(tmp_path, data, filename="first.json")
    _seed(tmp_path, data, filename="second.json")

    assert CombinationTrait.objects.count() == 1
    assert Trait.objects.filter(name="Compassion", locale="en").count() == 1
