"""
Tests für `apps.quiz.anonymous_result` (Task 2.11, FR-T15/FR-T16, D-18).

Reine Signier-/Prüf-Logik, unabhängig von Views — die Views selbst
kommen in test_claim_anonymous_result.py.
"""

import pytest
from django.conf import settings
from django.core import signing
from django.test import override_settings

from apps.quiz import anonymous_result

pytestmark = pytest.mark.django_db


def test_a_freshly_signed_token_round_trips():
    scores = {"W": 5, "U": 3, "B": 0, "R": 0, "G": 0}
    token = anonymous_result.sign(questionnaire_version=1, scores=scores)

    assert anonymous_result.unsign(token) == (1, scores)


def test_garbage_is_rejected():
    assert anonymous_result.unsign("not-a-valid-token") is None


VALID_SCORES = {"W": 5, "U": 3, "B": 0, "R": 0, "G": 0}


def test_a_tampered_token_is_rejected():
    token = anonymous_result.sign(questionnaire_version=1, scores=VALID_SCORES)
    tampered = token[:-1] + ("a" if token[-1] != "a" else "b")

    assert anonymous_result.unsign(tampered) is None


def test_an_expired_token_is_rejected():
    with override_settings(QUIZ_ANONYMOUS_RESULT_MAX_AGE=0):
        token = anonymous_result.sign(questionnaire_version=1, scores=VALID_SCORES)

    with override_settings(QUIZ_ANONYMOUS_RESULT_MAX_AGE=-1):
        assert anonymous_result.unsign(token) is None


def test_a_token_signed_with_a_different_salt_is_rejected():
    token = signing.dumps(
        {"questionnaire_version": 1, "scores": VALID_SCORES}, salt="something-else"
    )

    assert anonymous_result.unsign(token) is None


@pytest.mark.parametrize(
    "scores",
    [
        {"W": 5},  # unvollständig
        {"W": 5, "U": 3, "B": 0, "R": 0, "G": 0, "extra": 1},  # zusätzliches Feld
        {"W": 5, "U": 3, "B": 0, "R": 0, "G": "0"},  # falscher Typ
        {"W": -1, "U": 3, "B": 0, "R": 0, "G": 0},  # negativ
        "not-a-dict",
        None,
    ],
)
def test_malformed_scores_are_rejected(scores):
    token = signing.dumps(
        {"questionnaire_version": 1, "scores": scores}, salt=settings.QUIZ_ANONYMOUS_RESULT_SALT
    )

    assert anonymous_result.unsign(token) is None


def test_a_non_integer_questionnaire_version_is_rejected():
    token = signing.dumps(
        {"questionnaire_version": "1", "scores": {"W": 5, "U": 0, "B": 0, "R": 0, "G": 0}},
        salt=settings.QUIZ_ANONYMOUS_RESULT_SALT,
    )

    assert anonymous_result.unsign(token) is None
