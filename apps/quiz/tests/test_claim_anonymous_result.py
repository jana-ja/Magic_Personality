"""
Tests für „Ergebnis ohne Anmeldung" (Task 2.11, FR-T15/FR-T16, D-18).

Die Signier-/Prüf-Logik selbst hat eigene, feingranulare Tests in
test_anonymous_result.py — hier geht es um das Zusammenspiel von
`take_test()` (setzt das Token) und `claim_anonymous_result()` (löst
es nach Login/Registrierung ein).
"""

import pytest

from apps.accounts.models import ColorAssignment, Profile, User
from apps.quiz import anonymous_result
from apps.quiz.evaluation import evaluate_combination
from apps.quiz.models import TestResult
from apps.quiz.scoring import tally

pytestmark = pytest.mark.django_db

TAKE_TEST_URL = "/quiz/"
CLAIM_URL = "/quiz/results/claim/"


def _field_name(question):
    return f"question_{question.pk}"


def _submit_all(client, questionnaire):
    questions = list(questionnaire.questions.all())
    chosen_answers = [question.answer_options.first() for question in questions]
    data = {
        _field_name(question): answer.pk
        for question, answer in zip(questions, chosen_answers, strict=True)
    }
    response = client.post(TAKE_TEST_URL, data)
    return response, tally(chosen_answers)


@pytest.fixture
def user():
    user = User.objects.create_user(email="alex@example.com", password="a-long-enough-password")
    Profile.objects.create(user=user, nickname="alex")
    return user


# Ergebnisseite bietet das Token an (FR-T15) --------------------------------


def test_anonymous_result_page_stores_the_token_in_local_storage(
    gated_client, published_questionnaire
):
    response, _scores = _submit_all(gated_client, published_questionnaire)

    assert "localStorage.setItem" in response.content.decode()
    assert "mp_pending_quiz_result" in response.content.decode()


def test_logged_in_result_page_does_not_set_a_token(gated_client, published_questionnaire, user):
    gated_client.force_login(user)

    response, _scores = _submit_all(gated_client, published_questionnaire)

    assert "localStorage.setItem" not in response.content.decode()


# Einlösen nach Login/Registrierung (FR-T16) --------------------------------


def test_claim_requires_login(gated_client):
    token = anonymous_result.sign(
        questionnaire_version=1, scores={"W": 5, "U": 0, "B": 0, "R": 0, "G": 0}
    )

    response = gated_client.post(CLAIM_URL, {"token": token})

    assert response.status_code == 302
    assert response.url.startswith("/accounts/login/")
    assert not TestResult.objects.exists()


def test_claim_only_accepts_post(gated_client, user):
    gated_client.force_login(user)

    response = gated_client.get(CLAIM_URL)

    assert response.status_code == 405


def test_a_valid_token_is_saved_to_the_history_and_offered_for_adoption(
    gated_client, published_questionnaire, user
):
    _response, scores = _submit_all(gated_client, published_questionnaire)
    token = anonymous_result.sign(
        questionnaire_version=published_questionnaire.version, scores=scores
    )
    combination = evaluate_combination(scores)

    gated_client.force_login(user)
    response = gated_client.post(CLAIM_URL, {"token": token})

    assert response.status_code == 200
    assert "Add these colors to my profile" in response.content.decode()

    result = TestResult.objects.get(profile=user.profile)
    assert result.scores == scores
    assert result.result_colors == combination.code
    assert result.questionnaire_version == published_questionnaire.version


def test_claimed_result_page_does_not_set_a_new_token(gated_client, published_questionnaire, user):
    """Die eingelöste Ergebnisseite trägt kein `anonymous_token` mehr
    im Kontext — sonst würde sich dasselbe Ergebnis endlos neu in
    localStorage schreiben."""
    _response, scores = _submit_all(gated_client, published_questionnaire)
    token = anonymous_result.sign(
        questionnaire_version=published_questionnaire.version, scores=scores
    )

    gated_client.force_login(user)
    response = gated_client.post(CLAIM_URL, {"token": token})

    assert "localStorage.setItem" not in response.content.decode()


# Manipulierte oder veraltete Daten werden abgewiesen (Roadmap 2.11) --------


def test_missing_token_is_rejected_without_error(gated_client, user):
    gated_client.force_login(user)

    response = gated_client.post(CLAIM_URL, {})

    assert response.status_code == 302
    assert not TestResult.objects.exists()


def test_tampered_token_is_rejected_without_error(gated_client, user):
    token = anonymous_result.sign(
        questionnaire_version=1, scores={"W": 5, "U": 0, "B": 0, "R": 0, "G": 0}
    )
    tampered = token[:-1] + ("a" if token[-1] != "a" else "b")
    gated_client.force_login(user)

    response = gated_client.post(CLAIM_URL, {"token": tampered})

    assert response.status_code == 302
    assert not TestResult.objects.exists()


def test_expired_token_is_rejected_without_error(gated_client, settings, user):
    settings.QUIZ_ANONYMOUS_RESULT_MAX_AGE = 0
    token = anonymous_result.sign(
        questionnaire_version=1, scores={"W": 5, "U": 0, "B": 0, "R": 0, "G": 0}
    )
    settings.QUIZ_ANONYMOUS_RESULT_MAX_AGE = -1
    gated_client.force_login(user)

    response = gated_client.post(CLAIM_URL, {"token": token})

    assert response.status_code == 302
    assert not TestResult.objects.exists()


def test_claiming_does_not_by_itself_change_the_profile_colors(
    gated_client, published_questionnaire, user
):
    """FR-T14/D-07: die Historie füllt sich automatisch, die
    Profil-Übernahme bleibt ein separates Angebot."""
    _response, scores = _submit_all(gated_client, published_questionnaire)
    token = anonymous_result.sign(
        questionnaire_version=published_questionnaire.version, scores=scores
    )

    gated_client.force_login(user)
    gated_client.post(CLAIM_URL, {"token": token})

    assert not ColorAssignment.objects.filter(profile=user.profile).exists()
