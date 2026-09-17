"""
Tests für „Test durchführen" (Task 2.8, FR-T7 bis FR-T9).

Nutzt `published_questionnaire` (conftest.py) — ein frei erfundener,
kleiner Fragebogen. Die echten 20 Fragen kommen erst mit Task 2.7; der
hier geprüfte Mechanismus kennt "20" nirgends fest verdrahtet.
"""

import pytest

pytestmark = pytest.mark.django_db

TAKE_TEST_URL = "/quiz/"


def _field_name(question):
    return f"question_{question.pk}"


def test_returns_404_without_a_published_questionnaire(gated_client):
    response = gated_client.get(TAKE_TEST_URL)

    assert response.status_code == 404


def test_page_is_reachable_without_login(gated_client, published_questionnaire):
    """FR-T-Bereich der Roadmap: "auch ohne Login durchführbar"."""
    response = gated_client.get(TAKE_TEST_URL)

    assert response.status_code == 200
    assert not response.wsgi_request.user.is_authenticated


def test_page_shows_every_question_and_its_answers(gated_client, published_questionnaire):
    response = gated_client.get(TAKE_TEST_URL)

    html = response.content.decode()
    for question in published_questionnaire.questions.all():
        assert question.text in html
        for answer in question.answer_options.all():
            assert answer.text in html


def test_submitting_all_answers_succeeds(gated_client, published_questionnaire):
    questions = list(published_questionnaire.questions.all())
    data = {_field_name(question): question.answer_options.first().pk for question in questions}

    response = gated_client.post(TAKE_TEST_URL, data)

    assert response.status_code == 200
    assert "Your results" in response.content.decode()


def test_incomplete_submission_is_rejected(gated_client, published_questionnaire):
    """FR-T9: Abgabe erst möglich, wenn alle Fragen beantwortet sind."""
    questions = list(published_questionnaire.questions.all())
    data = {
        _field_name(question): question.answer_options.first().pk
        for question in questions[:-1]  # die letzte Frage bleibt unbeantwortet
    }

    response = gated_client.post(TAKE_TEST_URL, data)

    assert response.status_code == 200
    assert "Your results" not in response.content.decode()
    assert "Please choose an answer for every question." in response.content.decode()


def test_incomplete_submission_keeps_the_already_chosen_answers(
    gated_client, published_questionnaire
):
    """Roadmap 2.8: "Antworten bleiben erhalten"."""
    questions = list(published_questionnaire.questions.all())
    chosen_answer = questions[0].answer_options.first()
    data = {_field_name(questions[0]): chosen_answer.pk}

    response = gated_client.post(TAKE_TEST_URL, data)

    html = response.content.decode()
    assert f'value="{chosen_answer.pk}"' in html
    assert html.count(" checked") == 1


def test_submission_computes_the_correct_tally(gated_client, published_questionnaire):
    questions = list(published_questionnaire.questions.all())
    chosen = [
        question.answer_options.get(color=question.answer_options.first().color)
        for question in questions
    ]
    data = {_field_name(q): a.pk for q, a in zip(questions, chosen, strict=True)}

    response = gated_client.post(TAKE_TEST_URL, data)

    html = response.content.decode()
    for color in {answer.color for answer in chosen}:
        count = sum(1 for answer in chosen if answer.color == color)
        assert f"<dt>{color}</dt>" in html
        assert f"<dd>{count}</dd>" in html


def test_an_answer_from_a_different_question_is_rejected(gated_client, published_questionnaire):
    """Jedes Feld ist auf die AnswerOptions der eigenen Frage begrenzt
    (`AnswerChoiceField(queryset=question.answer_options...)`)."""
    questions = list(published_questionnaire.questions.all())
    foreign_answer = questions[1].answer_options.first()

    response = gated_client.post(TAKE_TEST_URL, {_field_name(questions[0]): foreign_answer.pk})

    assert response.status_code == 200
    assert "Your results" not in response.content.decode()
