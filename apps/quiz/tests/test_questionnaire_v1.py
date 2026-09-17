"""
Prüft die echte Seed-Datei seeds/questionnaire_v1.json (Task 2.7,
FR-T1 bis FR-T4, D-60) — nicht Beispieldaten (ARCHITECTURE.md §10).

Die Balance-Regeln sind harte Anforderungen. Die Regeln gegen erkennbare
Muster (Antwortposition, direkte Wiederholung, Antwortlänge) sichern
die Qualitätsregeln aus D-60 ab, soweit sie sich automatisch prüfen
lassen; ob beide Antworten gleich attraktiv sind, kann kein Test sehen.
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

SEED_PATH = Path(settings.BASE_DIR) / "seeds" / "questionnaire_v1.json"
COLORS = [code for code, _label in Color.Code.choices]
PAIRS = {frozenset(pair) for pair in itertools.combinations(COLORS, 2)}
DIMENSIONS = {value for value, _label in Question.Dimension.choices}

QUESTION_COUNT = len(PAIRS) * len(DIMENSIONS)  # 30
APPEARANCES_PER_COLOR = QUESTION_COUNT * 2 // len(COLORS)  # 12

# Längere Antwort höchstens so viel länger als die kürzere (in Zeichen).
MAX_ANSWER_LENGTH_RATIO = 1.3

COLOR_WORDS = re.compile(r"\b(white|blue|black|red|green|colou?rs?|mana)\b", re.IGNORECASE)


@pytest.fixture(scope="module")
def questions():
    return json.loads(SEED_PATH.read_text(encoding="utf-8"))["questions"]


def _pair(question):
    return frozenset(answer["color"] for answer in question["answers"])


# Aufbau (FR-T1) --------------------------------------------------------------


def test_has_expected_number_of_questions_in_order(questions):
    assert [q["position"] for q in questions] == list(range(1, QUESTION_COUNT + 1))


def test_every_question_has_two_answers_of_different_colors(questions):
    for q in questions:
        assert len(q["answers"]) == 2, q["position"]
        assert len(_pair(q)) == 2, q["position"]


# Balance (FR-T3, FR-T4) ------------------------------------------------------


def test_every_pair_appears_exactly_once_per_dimension(questions):
    for dimension in DIMENSIONS:
        pairs = [_pair(q) for q in questions if q["dimension"] == dimension]
        assert Counter(pairs) == Counter(PAIRS), dimension


def test_every_color_appears_equally_often(questions):
    appearances = Counter(color for q in questions for color in _pair(q))
    assert appearances == dict.fromkeys(COLORS, APPEARANCES_PER_COLOR)


# Keine erkennbaren Muster (D-60) ---------------------------------------------


def test_every_color_is_listed_first_equally_often(questions):
    firsts = Counter(q["answers"][0]["color"] for q in questions)
    assert firsts == dict.fromkeys(COLORS, APPEARANCES_PER_COLOR // 2)


def test_no_pair_always_lists_the_same_color_first(questions):
    for pair in PAIRS:
        firsts = {q["answers"][0]["color"] for q in questions if _pair(q) == pair}
        assert len(firsts) == 2, sorted(pair)


def test_consecutive_questions_share_no_color(questions):
    for previous, current in itertools.pairwise(questions):
        assert not _pair(previous) & _pair(current), current["position"]


def test_answers_have_similar_length(questions):
    for q in questions:
        lengths = sorted(len(answer["text"]) for answer in q["answers"])
        assert lengths[1] <= lengths[0] * MAX_ANSWER_LENGTH_RATIO, q["position"]


def test_no_text_names_a_color(questions):
    texts = [q["text"] for q in questions] + [a["text"] for q in questions for a in q["answers"]]
    assert [text for text in texts if COLOR_WORDS.search(text)] == []


# Import ----------------------------------------------------------------------


@pytest.mark.django_db
def test_seed_file_imports(questions):
    call_command("seed_questionnaire", questionnaire_version=1, locale="en")
    questionnaire = Questionnaire.objects.get(version=1)
    assert questionnaire.question_count == QUESTION_COUNT
    assert questionnaire.questions.count() == QUESTION_COUNT
