"""
Tests für die Hauptnavigation im Kopfbereich (Task 2.15, D-64).
"""

import re

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import Profile, User
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


@pytest.fixture
def user():
    user = User.objects.create_user(email="alex@example.com", password="a-long-enough-password")
    Profile.objects.create(user=user, nickname="alex")
    return user


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


# Search-Link (nachgetragen, siehe D-68): nur für Angemeldete, weil die
# Views selbst @login_required sind (FR-S1 bis FR-S3) — ein Link ins
# Leere für Gäste wäre irreführend. -------------------------------------


def test_search_link_is_hidden_for_anonymous_visitors(gated_client):
    html = gated_client.get(reverse("about")).content.decode()

    assert f'href="{reverse("social:search")}"' not in html


def test_search_link_is_shown_for_logged_in_visitors(gated_client, user):
    gated_client.force_login(user)

    html = gated_client.get(reverse("about")).content.decode()

    assert f'href="{reverse("social:search")}"' in html


@pytest.mark.parametrize(
    "url_name,url_kwargs",
    [
        ("social:search", {}),
        ("social:search_colors", {}),
        ("social:profile_detail", {"nickname": "jamie"}),
    ],
)
def test_search_is_marked_current_on_every_social_page(gated_client, user, url_name, url_kwargs):
    Profile.objects.create(nickname="jamie")
    gated_client.force_login(user)

    html = gated_client.get(reverse(url_name, kwargs=url_kwargs)).content.decode()

    assert _current_links(html) == [reverse("social:search")]
