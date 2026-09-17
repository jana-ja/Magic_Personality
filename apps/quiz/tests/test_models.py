"""
Tests für das Fragebogen-Datenmodell aus Task 2.6.

Deckt die Punkte aus der Definition of Done in docs/ROADMAP.md ab, die
das Modell selbst betreffen (Balance und Auswertung kommen erst mit
Task 2.7/2.9 und werden dort gegen die echte Seed-Datei getestet).
"""

import pytest
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError
from django.utils import timezone

from apps.accounts.models import Profile
from apps.quiz.models import AnswerOption, Question, Questionnaire, TestResult

pytestmark = pytest.mark.django_db


def test_questionnaire_is_not_published_by_default():
    questionnaire = Questionnaire.objects.create(version=1, question_count=0)

    assert questionnaire.is_published is False


def test_questionnaire_is_published_once_published_at_is_set():
    questionnaire = Questionnaire.objects.create(version=1, question_count=0)
    questionnaire.published_at = timezone.now()
    questionnaire.save()

    assert questionnaire.is_published is True


def test_question_position_is_unique_per_questionnaire_and_locale():
    questionnaire = Questionnaire.objects.create(version=1, question_count=1)
    Question.objects.create(
        questionnaire=questionnaire, position=1, text="A?", dimension=Question.Dimension.INNER
    )

    with pytest.raises(IntegrityError):
        Question.objects.create(
            questionnaire=questionnaire,
            position=1,
            text="B?",
            dimension=Question.Dimension.OUTER,
        )


def test_answer_option_color_is_unique_per_question():
    questionnaire = Questionnaire.objects.create(version=1, question_count=1)
    question = Question.objects.create(
        questionnaire=questionnaire, position=1, text="A?", dimension=Question.Dimension.INNER
    )
    AnswerOption.objects.create(question=question, text="Yes", color="W")

    with pytest.raises(IntegrityError):
        AnswerOption.objects.create(question=question, text="No", color="W")


def test_answer_option_locale_must_match_its_question():
    questionnaire = Questionnaire.objects.create(version=1, question_count=1)
    question = Question.objects.create(
        questionnaire=questionnaire,
        position=1,
        text="A?",
        dimension=Question.Dimension.INNER,
        locale="en",
    )
    answer = AnswerOption(question=question, text="Yes", color="W", locale="de")

    with pytest.raises(ValidationError):
        answer.full_clean()


def test_test_result_stores_scores_and_result_colors():
    profile = Profile.objects.create(nickname="alex")
    result = TestResult.objects.create(
        profile=profile,
        questionnaire_version=1,
        scores={"W": 5, "U": 3, "B": 4, "R": 4, "G": 4},
        result_colors="W",
    )

    assert result.scores["W"] == 5
    assert result.result_colors == "W"
    assert result.taken_at is not None
