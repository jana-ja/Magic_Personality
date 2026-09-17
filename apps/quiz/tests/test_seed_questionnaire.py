"""
Tests für `manage.py seed_questionnaire` (Task 2.6, D-28, FR-T6).

Nutzt ausschließlich eigene, kleine Test-Fixtures über --path — die
echten 30 Fragen stehen in seeds/questionnaire_v1.json
(Task 2.7) und werden in test_questionnaire_v1.py geprüft.
"""

import json

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from apps.quiz.models import AnswerOption, Question, Questionnaire

pytestmark = pytest.mark.django_db


def _question(position=1, dimension="ACTION", text="A?", colors=("W", "U")):
    return {
        "position": position,
        "dimension": dimension,
        "text": text,
        "answers": [
            {"color": colors[0], "text": f"{text} option {colors[0]}"},
            {"color": colors[1], "text": f"{text} option {colors[1]}"},
        ],
    }


def _seed(tmp_path, data, *, version=1, locale="en", filename="questionnaire.json"):
    path = tmp_path / filename
    path.write_text(json.dumps(data), encoding="utf-8")
    call_command("seed_questionnaire", questionnaire_version=version, locale=locale, path=str(path))
    return path


def _seed_raises(tmp_path, data, *, version=1, locale="en"):
    path = tmp_path / "questionnaire.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(CommandError) as excinfo:
        call_command(
            "seed_questionnaire", questionnaire_version=version, locale=locale, path=str(path)
        )
    return str(excinfo.value)


# Grundlegende Fehlerfälle ---------------------------------------------------


def test_missing_version_argument_raises():
    with pytest.raises(CommandError):
        call_command("seed_questionnaire", locale="en")


def test_missing_file_raises_a_clear_error(tmp_path):
    missing = tmp_path / "does-not-exist.json"
    with pytest.raises(CommandError, match="nicht gefunden"):
        call_command("seed_questionnaire", questionnaire_version=1, locale="en", path=str(missing))


def test_invalid_json_raises_a_clear_error(tmp_path):
    path = tmp_path / "broken.json"
    path.write_text("{not valid json", encoding="utf-8")

    with pytest.raises(CommandError, match="kein gültiges JSON"):
        call_command("seed_questionnaire", questionnaire_version=1, locale="en", path=str(path))


def test_version_mismatch_between_argument_and_file_raises(tmp_path):
    message = _seed_raises(tmp_path, {"version": 2, "locale": "en", "questions": []}, version=1)
    assert "1" in message and "2" in message


def test_locale_mismatch_between_argument_and_file_raises(tmp_path):
    message = _seed_raises(tmp_path, {"version": 1, "locale": "de", "questions": []}, locale="en")
    assert "de" in message and "en" in message


def test_unknown_top_level_key_raises(tmp_path):
    message = _seed_raises(tmp_path, {"version": 1, "locale": "en", "questions": [], "extra": True})
    assert "extra" in message


def test_unknown_question_key_raises(tmp_path):
    entry = _question()
    entry["typo"] = True
    message = _seed_raises(tmp_path, {"version": 1, "locale": "en", "questions": [entry]})
    assert "typo" in message


def test_unknown_answer_key_raises(tmp_path):
    entry = _question()
    entry["answers"][0]["typo"] = True
    message = _seed_raises(tmp_path, {"version": 1, "locale": "en", "questions": [entry]})
    assert "typo" in message


def test_question_without_required_fields_raises(tmp_path):
    with pytest.raises(CommandError):
        _seed(tmp_path, {"version": 1, "locale": "en", "questions": [{"position": 1}]})


# Erfolgreicher Import --------------------------------------------------------


def test_seeding_creates_questionnaire_questions_and_answers(tmp_path):
    _seed(tmp_path, {"version": 1, "locale": "en", "questions": [_question()]})

    questionnaire = Questionnaire.objects.get(version=1)
    assert questionnaire.question_count == 1
    assert questionnaire.is_published is False

    question = Question.objects.get(questionnaire=questionnaire, position=1)
    assert question.dimension == "ACTION"
    assert question.locale == "en"
    assert AnswerOption.objects.filter(question=question).count() == 2


def test_seeding_twice_with_unchanged_content_does_not_duplicate(tmp_path):
    data = {"version": 1, "locale": "en", "questions": [_question()]}
    _seed(tmp_path, data)
    _seed(tmp_path, data)

    assert Questionnaire.objects.filter(version=1).count() == 1
    assert Question.objects.count() == 1
    assert AnswerOption.objects.count() == 2


def test_seeding_an_unpublished_version_again_may_change_content(tmp_path):
    _seed(tmp_path, {"version": 1, "locale": "en", "questions": [_question(text="Old?")]})
    _seed(tmp_path, {"version": 1, "locale": "en", "questions": [_question(text="New?")]})

    question = Question.objects.get(questionnaire__version=1, position=1)
    assert question.text == "New?"


# Veröffentlichung und Unveränderlichkeit (FR-T6) ----------------------------


def test_publishing_sets_published_at(tmp_path):
    _seed(
        tmp_path,
        {"version": 1, "locale": "en", "published": True, "questions": [_question()]},
    )

    questionnaire = Questionnaire.objects.get(version=1)
    assert questionnaire.is_published is True


def test_republishing_the_same_content_is_idempotent(tmp_path):
    data = {"version": 1, "locale": "en", "published": True, "questions": [_question()]}
    _seed(tmp_path, data)
    published_at = Questionnaire.objects.get(version=1).published_at

    _seed(tmp_path, data)

    assert Questionnaire.objects.get(version=1).published_at == published_at


def test_changing_a_question_of_a_published_version_raises(tmp_path):
    _seed(
        tmp_path,
        {"version": 1, "locale": "en", "published": True, "questions": [_question(text="Old?")]},
    )

    message = _seed_raises(
        tmp_path,
        {"version": 1, "locale": "en", "published": True, "questions": [_question(text="New?")]},
    )
    assert "veröffentlicht" in message

    assert Question.objects.get(questionnaire__version=1, position=1).text == "Old?"


def test_changing_an_answer_of_a_published_version_raises(tmp_path):
    _seed(
        tmp_path,
        {"version": 1, "locale": "en", "published": True, "questions": [_question()]},
    )

    changed = _question()
    changed["answers"][0]["text"] = "Something else"
    with pytest.raises(CommandError, match="veröffentlicht"):
        _seed(
            tmp_path,
            {"version": 1, "locale": "en", "published": True, "questions": [changed]},
        )


def test_adding_a_question_to_a_published_version_raises(tmp_path):
    _seed(
        tmp_path,
        {"version": 1, "locale": "en", "published": True, "questions": [_question(position=1)]},
    )

    with pytest.raises(CommandError, match="veröffentlicht"):
        _seed(
            tmp_path,
            {
                "version": 1,
                "locale": "en",
                "published": True,
                "questions": [_question(position=1), _question(position=2)],
            },
        )


def test_unpublishing_a_published_version_raises(tmp_path):
    _seed(
        tmp_path,
        {"version": 1, "locale": "en", "published": True, "questions": [_question()]},
    )

    with pytest.raises(CommandError, match="veröffentlicht"):
        _seed(
            tmp_path,
            {"version": 1, "locale": "en", "published": False, "questions": [_question()]},
        )
