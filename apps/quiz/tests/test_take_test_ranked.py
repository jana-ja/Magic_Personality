"""
Tests für das Format aus v2 (D-65): fünf Antworten je Frage, die beste
und die zweitbeste werden gewählt und geben 2 bzw. 1 Punkt.

Nutzt `published_ranked_questionnaire` (conftest.py).
"""

import pytest

from apps.quiz.forms import TakeTestForm

pytestmark = pytest.mark.django_db

TAKE_TEST_URL = "/quiz/"


def _answers(questionnaire):
    """Je Frage die Antworten in Anzeigereihenfolge."""
    return [
        (question, list(question.answer_options.all()))
        for question in questionnaire.questions.all()
    ]


def _data(picks):
    data = {}
    for question, best, second in picks:
        data[TakeTestForm.field_name(question, 0)] = best.pk
        if second is not None:
            data[TakeTestForm.field_name(question, 1)] = second.pk
    return data


def test_page_offers_best_and_second_best_for_every_answer(
    gated_client, published_ranked_questionnaire
):
    html = gated_client.get(TAKE_TEST_URL).content.decode()

    assert 'class="quiz-ranking"' in html
    for question, answers in _answers(published_ranked_questionnaire):
        assert f'name="{TakeTestForm.field_name(question, 0)}"' in html
        assert f'name="{TakeTestForm.field_name(question, 1)}"' in html
        assert html.count(f'name="{TakeTestForm.field_name(question, 1)}"') == len(answers)


def test_answers_are_shown_in_seed_order_not_by_color(gated_client, published_ranked_questionnaire):
    html = gated_client.get(TAKE_TEST_URL).content.decode()

    for _question, answers in _answers(published_ranked_questionnaire):
        offsets = [html.index(f'aria-hidden="true">{answer.text}<') for answer in answers]
        assert offsets == sorted(offsets)
        assert [answer.position for answer in answers] == list(range(len(answers)))


def test_best_answer_gives_two_points_and_second_best_one(
    gated_client, published_ranked_questionnaire
):
    (q1, a1), (q2, a2) = _answers(published_ranked_questionnaire)
    # Frage 1: G beste, W zweitbeste. Frage 2: W beste, B zweitbeste.
    w_in_q2 = next(answer for answer in a2 if answer.color == "W")
    data = _data([(q1, a1[0], a1[1]), (q2, w_in_q2, a2[0])])

    html = gated_client.post(TAKE_TEST_URL, data).content.decode()

    for color, points in {"W": 3, "G": 2, "B": 1, "U": 0, "R": 0}.items():
        assert f"<dt>{color}</dt>" in html
        assert f"<dt>{color}</dt>\n        <dd>{points}</dd>" in html


def test_same_answer_for_both_places_is_rejected(gated_client, published_ranked_questionnaire):
    (q1, a1), (q2, a2) = _answers(published_ranked_questionnaire)
    data = _data([(q1, a1[0], a1[0]), (q2, a2[0], a2[1])])

    html = gated_client.post(TAKE_TEST_URL, data).content.decode()

    assert "Your results" not in html
    assert "Please choose a different answer for each place." in html


def test_missing_second_best_is_rejected(gated_client, published_ranked_questionnaire):
    (q1, a1), (q2, a2) = _answers(published_ranked_questionnaire)
    data = _data([(q1, a1[0], a1[1]), (q2, a2[0], None)])

    html = gated_client.post(TAKE_TEST_URL, data).content.decode()

    assert "Your results" not in html
    assert "Please choose an answer for every question." in html
