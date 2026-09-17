"""
Fixtures, die mehrere Test-Dateien in apps/quiz/tests/ teilen.

`published_questionnaire` nutzt bewusst frei erfundene Dummy-Fragen
statt der echten 20 aus Task 2.7 (eigene Sitzung, noch nicht
geschrieben) — der Mechanismus aus Task 2.8 kennt die Zahl "20"
nirgends fest verdrahtet, sondern fragt immer nach *allen* Fragen der
aktuell veröffentlichten Version. Ein kleiner, frei erfundener
Fragebogen prüft also denselben Code-Pfad wie der echte.
"""

import pytest
from django.utils import timezone

from apps.quiz.models import AnswerOption, Question, Questionnaire

DUMMY_QUESTIONS = [
    ("INNER", "Something you care about is at risk. What is your first instinct?", ("W", "B")),
    ("OUTER", "How do you react when a plan falls apart?", ("U", "R")),
    ("FEELING", "What does a good day feel like?", ("G", "W")),
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
        AnswerOption.objects.create(
            question=question, color=colors[0], text=f"{text} ({colors[0]})"
        )
        AnswerOption.objects.create(
            question=question, color=colors[1], text=f"{text} ({colors[1]})"
        )
    return questionnaire
