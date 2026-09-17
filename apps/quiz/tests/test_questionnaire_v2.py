"""
Prüft die echte Seed-Datei seeds/questionnaire_v2.json (Task 2.16,
FR-T1 bis FR-T5, D-65) — nicht Beispieldaten (ARCHITECTURE.md §10).

Jede Frage bietet alle fünf Farben an; die Balance je Farbe ist damit
schon durch den Aufbau gegeben. Geprüft wird vor allem, dass keine
erkennbaren Muster entstehen (Antwortposition, Reihenfolge der
Dimensionen, Antwortlänge) — ob alle fünf Antworten gleich attraktiv
sind, kann kein Test sehen.
"""

import itertools
import json
import re
from collections import Counter
from pathlib import Path

import pytest
from django.conf import settings
from django.core.management import call_command

from apps.colors.models import Color
from apps.quiz.models import Question, Questionnaire

SEED_PATH = Path(settings.BASE_DIR) / "seeds" / "questionnaire_v2.json"
COLORS = [code for code, _label in Color.Code.choices]
DIMENSIONS = [value for value, _label in Question.Dimension.choices]

QUESTIONS_PER_DIMENSION = 5
QUESTION_COUNT = QUESTIONS_PER_DIMENSION * len(DIMENSIONS)  # 15

# Längste Antwort einer Frage höchstens so viel länger als die kürzeste.
MAX_ANSWER_LENGTH_RATIO = 1.35

COLOR_WORDS = re.compile(r"\b(white|blue|black|red|green|colou?rs?|mana)\b", re.IGNORECASE)


@pytest.fixture(scope="module")
def data():
    return json.loads(SEED_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def questions(data):
    return data["questions"]


def _colors(question):
    return [answer["color"] for answer in question["answers"]]


# Aufbau (FR-T1, FR-T5) -------------------------------------------------------


def test_scores_best_and_second_best_answer(data):
    assert data["choice_points"] == [2, 1]


def test_has_expected_number_of_questions_in_order(questions):
    assert [q["position"] for q in questions] == list(range(1, QUESTION_COUNT + 1))


def test_every_question_offers_each_color_exactly_once(questions):
    for q in questions:
        assert sorted(_colors(q)) == sorted(COLORS), q["position"]


def test_every_dimension_has_the_same_number_of_questions(questions):
    counts = Counter(q["dimension"] for q in questions)
    assert counts == dict.fromkeys(DIMENSIONS, QUESTIONS_PER_DIMENSION)


# Keine erkennbaren Muster (D-65) ---------------------------------------------


def test_dimensions_never_repeat_back_to_back(questions):
    for previous, current in itertools.pairwise(questions):
        assert previous["dimension"] != current["dimension"], current["position"]


def test_every_color_takes_every_answer_position_once_per_dimension(questions):
    for dimension in DIMENSIONS:
        rows = [_colors(q) for q in questions if q["dimension"] == dimension]
        for position in range(len(COLORS)):
            assert sorted(row[position] for row in rows) == sorted(COLORS), (dimension, position)


def test_consecutive_questions_never_show_a_color_at_the_same_position(questions):
    for previous, current in itertools.pairwise(questions):
        for a, b in zip(_colors(previous), _colors(current), strict=True):
            assert a != b, current["position"]


def test_answers_have_similar_length(questions):
    for q in questions:
        lengths = sorted(len(answer["text"]) for answer in q["answers"])
        assert lengths[-1] <= lengths[0] * MAX_ANSWER_LENGTH_RATIO, q["position"]


def test_no_text_names_a_color(questions):
    texts = [q["text"] for q in questions] + [a["text"] for q in questions for a in q["answers"]]
    assert [text for text in texts if COLOR_WORDS.search(text)] == []


# Import ----------------------------------------------------------------------


@pytest.mark.django_db
def test_seed_file_imports(data):
    call_command("seed_questionnaire", questionnaire_version=2, locale="en")

    questionnaire = Questionnaire.objects.get(version=2)
    assert questionnaire.question_count == QUESTION_COUNT
    assert questionnaire.choice_points == [2, 1]
    assert questionnaire.result_threshold == data["result_threshold"]
    assert questionnaire.is_published == data["published"]
    for question in questionnaire.questions.all():
        assert [a.color for a in question.answer_options.all()] == _colors(
            data["questions"][question.position - 1]
        )
