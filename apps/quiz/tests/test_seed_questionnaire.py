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


# Beste und zweitbeste Antwort (D-65) -----------------------------------------


def _ranked_question(position=1, colors=("G", "W", "R", "U", "B")):
    return {
        "position": position,
        "dimension": "ACTION",
        "text": f"Q{position}?",
        "answers": [{"color": color, "text": f"Q{position} {color}"} for color in colors],
    }


def _ranked(**overrides):
    data = {
        "version": 2,
        "locale": "en",
        "choice_points": [2, 1],
        "result_threshold": 4,
        "questions": [_ranked_question()],
    }
    data.update(overrides)
    return data


def test_choice_points_and_threshold_are_stored(tmp_path):
    _seed(tmp_path, _ranked(), version=2)

    questionnaire = Questionnaire.objects.get(version=2)
    assert questionnaire.choice_points == [2, 1]
    assert questionnaire.result_threshold == 4


def test_defaults_match_the_format_of_version_one(tmp_path):
    _seed(tmp_path, {"version": 1, "locale": "en", "questions": [_question()]})

    questionnaire = Questionnaire.objects.get(version=1)
    assert questionnaire.choice_points == [1]
    assert questionnaire.result_threshold == 2


def test_answer_positions_follow_the_seed_file(tmp_path):
    _seed(tmp_path, _ranked(), version=2)

    question = Question.objects.get(questionnaire__version=2)
    assert [answer.color for answer in question.answer_options.all()] == ["G", "W", "R", "U", "B"]
    assert [answer.position for answer in question.answer_options.all()] == [0, 1, 2, 3, 4]


@pytest.mark.parametrize("choice_points", [[], [1, 2], [2, 0], "2,1"])
def test_invalid_choice_points_raise(tmp_path, choice_points):
    message = _seed_raises(tmp_path, _ranked(choice_points=choice_points), version=2)
    assert "choice_points" in message


def test_negative_threshold_raises(tmp_path):
    message = _seed_raises(tmp_path, _ranked(result_threshold=-1), version=2)
    assert "result_threshold" in message


def test_a_question_needs_more_answers_than_choices(tmp_path):
    data = _ranked(questions=[_ranked_question(colors=("W", "U"))])
    message = _seed_raises(tmp_path, data, version=2)
    assert "Antworten" in message


def test_threshold_of_a_published_version_may_change(tmp_path):
    """R-4: `T` wird erst nach echten Durchläufen kalibriert (D-65)."""
    _seed(tmp_path, _ranked(published=True), version=2)

    _seed(tmp_path, _ranked(published=True, result_threshold=5), version=2)

    assert Questionnaire.objects.get(version=2).result_threshold == 5


def test_changing_choice_points_of_a_published_version_raises(tmp_path):
    _seed(tmp_path, _ranked(published=True), version=2)

    with pytest.raises(CommandError, match="veröffentlicht"):
        _seed(tmp_path, _ranked(published=True, choice_points=[3, 1]), version=2)


def test_reordering_answers_of_a_published_version_raises(tmp_path):
    _seed(tmp_path, _ranked(published=True), version=2)

    reordered = _ranked(
        published=True, questions=[_ranked_question(colors=("W", "G", "R", "U", "B"))]
    )
    with pytest.raises(CommandError, match="veröffentlicht"):
        _seed(tmp_path, reordered, version=2)
