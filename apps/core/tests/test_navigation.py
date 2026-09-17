"""
Tests für die Hauptnavigation im Kopfbereich (Task 2.15, D-64).
"""

import re

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.quiz.models import AnswerOption, Question, Questionnaire

pytestmark = pytest.mark.django_db


def _current_links(html):
    nav = re.search(r'<nav class="site-nav".*?</nav>', html, re.S).group(0)
    return re.findall(r'<a href="([^"]+)" aria-current="page"', nav)


@pytest.fixture
def published_questionnaire():
    questionnaire = Questionnaire.objects.create(
        version=1, question_count=1, published_at=timezone.now()
    )
    question = questionnaire.questions.create(
        position=1, text="A?", dimension=Question.Dimension.ACTION
    )
    for color in ("W", "U"):
        AnswerOption.objects.create(question=question, text=color, color=color)
    return questionnaire


def test_navigation_links_to_colors_and_test(gated_client):
    html = gated_client.get(reverse("about")).content.decode()

    assert f'href="{reverse("colors:index")}"' in html
    assert f'href="{reverse("quiz:take_test")}"' in html
    assert _current_links(html) == []


def test_colors_is_marked_current_on_every_colors_page(gated_client):
    for url in (reverse("colors:index"), reverse("colors:combination", args=["wu"])):
        html = gated_client.get(url).content.decode()
        assert _current_links(html) == [reverse("colors:index")], url


def test_test_is_marked_current_on_the_test_page(gated_client, published_questionnaire):
    html = gated_client.get(reverse("quiz:take_test")).content.decode()

    assert _current_links(html) == [reverse("quiz:take_test")]
