"""
Tests für „Ergebnis anzeigen und übernehmen" (Task 2.10, FR-T13/FR-T14).

Nutzt `published_questionnaire` (conftest.py) — ein frei erfundener,
kleiner Fragebogen; welche der 31 Kombinationen dabei herauskommt, wird
hier nie hart verdrahtet, sondern immer über `evaluate_combination()`
selbst nachgerechnet (die Auswertungsregel hat schon ihre eigenen
Tests in test_evaluation.py).
"""

import pytest

from apps.accounts.models import ColorAssignment, Profile, User
from apps.colors.models import ColorCombination
from apps.quiz.evaluation import evaluate_combination
from apps.quiz.models import TestResult
from apps.quiz.scoring import tally

pytestmark = pytest.mark.django_db

TAKE_TEST_URL = "/quiz/"


def _field_name(question):
    return f"question_{question.pk}"


def _submit_all(client, questionnaire, *, choose="first"):
    questions = list(questionnaire.questions.all())
    chosen_answers = [
        (question.answer_options.first() if choose == "first" else question.answer_options.last())
        for question in questions
    ]
    data = {
        _field_name(question): answer.pk
        for question, answer in zip(questions, chosen_answers, strict=True)
    }
    response = client.post(TAKE_TEST_URL, data)
    return response, tally([(answer, 1) for answer in chosen_answers])


@pytest.fixture
def user():
    user = User.objects.create_user(email="alex@example.com", password="a-long-enough-password")
    Profile.objects.create(user=user, nickname="alex")
    return user


# FR-T13: Name, Punkte, Link ------------------------------------------------


def test_result_page_shows_the_points_of_all_five_colors(gated_client, published_questionnaire):
    response, scores = _submit_all(gated_client, published_questionnaire)

    html = response.content.decode()
    for code, points in scores.items():
        assert f"<dt>{code}</dt>" in html
        assert f"<dd>{points}</dd>" in html


def test_result_page_links_to_the_matching_color_infos_page(gated_client, published_questionnaire):
    response, scores = _submit_all(gated_client, published_questionnaire)
    combination = evaluate_combination(scores, threshold=published_questionnaire.result_threshold)

    assert f'href="/colors/{combination.code.lower()}/"' in response.content.decode()


# FR-T14: eingeloggt landet das Ergebnis automatisch in der Historie --------


def test_logged_in_submission_is_saved_to_the_history(gated_client, published_questionnaire, user):
    gated_client.force_login(user)

    _, scores = _submit_all(gated_client, published_questionnaire)
    combination = evaluate_combination(scores, threshold=published_questionnaire.result_threshold)

    result = TestResult.objects.get(profile=user.profile)
    assert result.scores == scores
    assert result.result_colors == combination.code
    assert result.questionnaire_version == published_questionnaire.version


def test_anonymous_submission_is_not_saved_anywhere(gated_client, published_questionnaire):
    _submit_all(gated_client, published_questionnaire)

    assert not TestResult.objects.exists()


def test_anonymous_result_page_does_not_offer_to_adopt_the_colors(
    gated_client, published_questionnaire
):
    response, _scores = _submit_all(gated_client, published_questionnaire)

    assert "Add these colors to my profile" not in response.content.decode()


def test_logged_in_result_page_offers_to_adopt_the_colors(
    gated_client, published_questionnaire, user
):
    gated_client.force_login(user)

    response, _scores = _submit_all(gated_client, published_questionnaire)

    assert "Add these colors to my profile" in response.content.decode()


# Übernahme ins Profil: angeboten, nicht erzwungen (FR-T14, FR-P5, D-07) ----


def test_not_adopting_leaves_the_profile_without_a_color_assignment(
    gated_client, published_questionnaire, user
):
    gated_client.force_login(user)

    _submit_all(gated_client, published_questionnaire)

    assert not ColorAssignment.objects.filter(profile=user.profile).exists()


def test_adopting_the_result_sets_source_self_test_and_the_reference(
    gated_client, published_questionnaire, user
):
    gated_client.force_login(user)
    _submit_all(gated_client, published_questionnaire)
    result = TestResult.objects.get(profile=user.profile)

    response = gated_client.post(f"/quiz/results/{result.pk}/adopt/")

    assert response.status_code == 302
    assignment = ColorAssignment.objects.get(profile=user.profile)
    assert assignment.source == ColorAssignment.Source.SELF_TEST
    assert assignment.test_result == result
    assert assignment.combination.code == result.result_colors


def test_adopting_overwrites_a_previous_manual_assignment(
    gated_client, published_questionnaire, user
):
    ColorAssignment.objects.create(
        profile=user.profile,
        author_profile=user.profile,
        combination=ColorCombination.objects.get(code="WU", locale="en"),
        source=ColorAssignment.Source.SELF_MANUAL,
    )
    gated_client.force_login(user)
    _submit_all(gated_client, published_questionnaire)
    result = TestResult.objects.get(profile=user.profile)

    gated_client.post(f"/quiz/results/{result.pk}/adopt/")

    assignment = ColorAssignment.objects.get(profile=user.profile)
    assert assignment.source == ColorAssignment.Source.SELF_TEST
    assert assignment.test_result == result


def test_adopt_requires_login(gated_client, published_questionnaire):
    _submit_all(gated_client, published_questionnaire)

    # Kein Login -> keine Historie, also auch kein adoptierbares Ergebnis;
    # ein erfundener pk muss trotzdem zur Login-Seite führen, nicht zu 500.
    response = gated_client.post("/quiz/results/999999/adopt/")

    assert response.status_code == 302
    assert response.url.startswith("/accounts/login/")


def test_adopt_rejects_someone_elses_result(gated_client, published_questionnaire, user):
    other_user = User.objects.create_user(
        email="other@example.com", password="a-long-enough-password"
    )
    Profile.objects.create(user=other_user, nickname="other")

    gated_client.force_login(other_user)
    _submit_all(gated_client, published_questionnaire)
    result = TestResult.objects.get(profile=other_user.profile)

    gated_client.force_login(user)
    response = gated_client.post(f"/quiz/results/{result.pk}/adopt/")

    assert response.status_code == 404
    assert not ColorAssignment.objects.filter(profile=user.profile).exists()


def test_adopt_only_accepts_post(gated_client, published_questionnaire, user):
    gated_client.force_login(user)
    _submit_all(gated_client, published_questionnaire)
    result = TestResult.objects.get(profile=user.profile)

    response = gated_client.get(f"/quiz/results/{result.pk}/adopt/")

    assert response.status_code == 405
