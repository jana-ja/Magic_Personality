"""Tests für die Punkte-Zählung (Task 2.8, FR-T5, D-65)."""

import pytest

from apps.quiz.models import AnswerOption, Question, Questionnaire
from apps.quiz.scoring import tally

pytestmark = pytest.mark.django_db


@pytest.fixture
def answers():
    questionnaire = Questionnaire.objects.create(version=1, question_count=2)
    question_1 = Question.objects.create(
        questionnaire=questionnaire, position=1, text="Q1", dimension="ACTION"
    )
    question_2 = Question.objects.create(
        questionnaire=questionnaire, position=2, text="Q2", dimension="ACTION"
    )
    return [
        AnswerOption.objects.create(question=question_1, color="W", text="a"),
        AnswerOption.objects.create(question=question_2, color="W", text="b"),
        AnswerOption.objects.create(question=question_1, color="U", text="c"),
    ]


def test_every_color_appears_even_when_never_chosen(answers):
    scores = tally([(answers[0], 1)])

    assert scores == {"W": 1, "U": 0, "B": 0, "R": 0, "G": 0}


def test_counts_one_point_per_answer(answers):
    scores = tally([(answers[0], 1), (answers[1], 1), (answers[2], 1)])

    assert scores == {"W": 2, "U": 1, "B": 0, "R": 0, "G": 0}


def test_no_answers_yields_all_zeros():
    assert tally([]) == {"W": 0, "U": 0, "B": 0, "R": 0, "G": 0}


def test_counts_the_points_given_per_answer(answers):
    """D-65: beste Antwort 2 Punkte, zweitbeste 1 Punkt."""
    scores = tally([(answers[0], 2), (answers[2], 1)])

    assert scores == {"W": 2, "U": 1, "B": 0, "R": 0, "G": 0}
