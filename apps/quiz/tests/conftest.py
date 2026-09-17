"""
Fixtures, die mehrere Test-Dateien in apps/quiz/tests/ teilen.

`published_questionnaire` nutzt bewusst frei erfundene Dummy-Fragen
statt der echten 30 aus seeds/questionnaire_v1.json (Task 2.7) — der
Mechanismus aus Task 2.8 kennt die Fragenzahl nirgends fest
verdrahtet, sondern fragt immer nach *allen* Fragen der
aktuell veröffentlichten Version. Ein kleiner, frei erfundener
Fragebogen prüft also denselben Code-Pfad wie der echte.
"""

import pytest
from django.utils import timezone

from apps.quiz.models import AnswerOption, Question, Questionnaire

DUMMY_QUESTIONS = [
    ("ACTION", "Something you care about is at risk. What is your first instinct?", ("W", "B")),
    ("MOTIVATION", "How do you react when a plan falls apart?", ("U", "R")),
    ("PERCEPTION", "What does a good day feel like?", ("G", "W")),
]


@pytest.fixture
def published_questionnaire(db):
    questionnaire = Questionnaire.objects.create(
        version=1, question_count=len(DUMMY_QUESTIONS), published_at=timezone.now()
    )
    for position, (dimension, text, colors) in enumerate(DUMMY_QUESTIONS, start=1):
        question = Question.objects.create(
            questionnaire=questionnaire, position=position, text=text, dimension=dimension
        )
        for position, color in enumerate(colors):
            AnswerOption.objects.create(
                question=question, position=position, color=color, text=f"{text} ({color})"
            )
    return questionnaire


RANKED_QUESTIONS = [
    ("ACTION", "Ranked question one?", ("G", "W", "R", "U", "B")),
    ("MOTIVATION", "Ranked question two?", ("B", "R", "U", "G", "W")),
]


@pytest.fixture
def published_ranked_questionnaire(db):
    """Wie `published_questionnaire`, aber im Format von v2 (D-65):
    fünf Antworten je Frage, beste und zweitbeste werden gewählt."""
    questionnaire = Questionnaire.objects.create(
        version=2,
        question_count=len(RANKED_QUESTIONS),
        published_at=timezone.now(),
        choice_points=[2, 1],
        result_threshold=4,
    )
    for position, (dimension, text, colors) in enumerate(RANKED_QUESTIONS, start=1):
        question = Question.objects.create(
            questionnaire=questionnaire, position=position, text=text, dimension=dimension
        )
        for answer_position, color in enumerate(colors):
            AnswerOption.objects.create(
                question=question,
                position=answer_position,
                color=color,
                text=f"{text} ({color})",
            )
    return questionnaire
