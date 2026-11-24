"""
Tests für „Ergebnis anzeigen und übernehmen" (Task 2.10, FR-T13/FR-T14).

Nutzt `published_questionnaire` (conftest.py) — ein frei erfundener,
kleiner Fragebogen; welche der 31 Kombinationen dabei herauskommt, wird
hier nie hart verdrahtet, sondern immer über `evaluate_combination()`
selbst nachgerechnet (die Auswertungsregel hat schon ihre eigenen
Tests in test_evaluation.py).
"""

import re

import pytest

from apps.accounts.models import ColorAssignment, Profile, User
from apps.colors import pentagon
from apps.colors.models import Color, ColorCombination
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


def _points_per_color(html):
    """Buchstabe -> Punkte aus den Balken der Ergebnisseite (colors/_score_bars.html)."""
    pattern = r'score-bar__label">(\w)</span>.*?score-bar__value">(\d+)</span>'
    pairs = re.findall(pattern, html, re.S)
    return {code: int(points) for code, points in pairs}


@pytest.fixture
def user():
    user = User.objects.create_user(email="alex@example.com", password="a-long-enough-password")
    Profile.objects.create(user=user, nickname="alex")
    return user


# FR-T13: Name, Punkte, Link ------------------------------------------------


def test_result_page_shows_the_points_of_all_five_colors(gated_client, published_questionnaire):
    response, scores = _submit_all(gated_client, published_questionnaire)

    shown = _points_per_color(response.content.decode())
    assert shown == {code: scores.get(code, 0) for code in "WUBRG"}


def test_result_page_links_to_the_matching_color_infos_page(gated_client, published_questionnaire):
    response, scores = _submit_all(gated_client, published_questionnaire)
    combination = evaluate_combination(scores, threshold=published_questionnaire.result_threshold)

    assert f'href="/colors/{combination.code.lower()}/"' in response.content.decode()


# Punkte als Farbbalken, wie in der Colors-Karte des Profils (D-70, NFR-6) ---


def _score_bars(html):
    return re.search(r'<ul class="score-bars"[^>]*>.*?</ul>', html, re.S).group(0)


def test_result_page_shows_the_score_bars_in_wubrg_order(gated_client, published_questionnaire):
    response, scores = _submit_all(gated_client, published_questionnaire)

    bars = _score_bars(response.content.decode())
    labels = re.findall(r'score-bar__label">(\w)</span>', bars)
    values = re.findall(r'score-bar__value">(\d+)</span>', bars)
    assert labels == ["W", "U", "B", "R", "G"]
    assert values == [str(scores.get(code, 0)) for code in labels]


def test_result_page_bars_are_relative_to_the_highest_score(gated_client, published_questionnaire):
    response, scores = _submit_all(gated_client, published_questionnaire)

    top = max(scores.values())
    expected = [str(round(scores.get(code, 0) / top * 100)) for code in "WUBRG"]
    bars = _score_bars(response.content.decode())
    assert re.findall(r"--bar-width: (\d+)%", bars) == expected


def test_result_page_bars_use_the_halo_color_of_each_corner(gated_client, published_questionnaire):
    response, _scores = _submit_all(gated_client, published_questionnaire)

    bars = _score_bars(response.content.decode())
    expected = [pentagon.halo_color(code, Color.objects.get(code=code).hex) for code in "WUBRG"]
    assert re.findall(r"--bar-color: ([^;]+);", bars) == expected


def test_result_page_bars_name_each_color_for_screen_readers(gated_client, published_questionnaire):
    response, _scores = _submit_all(gated_client, published_questionnaire)

    bars = _score_bars(response.content.decode())
    assert "aria-label=" in bars.split(">")[0]
    assert bars.count('class="visually-hidden"') == 5


# Banner in den Farben der Kombination, wie im Profilkopf (D-73, NFR-6) -----


def _banner(html):
    return re.search(r'<div class="profile-banner[^"]*".*?</div>', html, re.S).group(0)


def test_result_page_shows_a_banner_stripe_per_color_of_the_combination(
    gated_client, published_questionnaire
):
    response, scores = _submit_all(gated_client, published_questionnaire)
    combination = evaluate_combination(scores, threshold=published_questionnaire.result_threshold)
    hex_by_code = dict(Color.objects.values_list("code", "hex"))

    banner = _banner(response.content.decode())

    hexes = re.findall(r"--segment-color: (#[0-9A-Fa-f]{6})", banner)
    assert hexes == [hex_by_code[code] for code in combination.color_codes]
    assert "profile-banner__stripe--neutral" not in banner


def test_result_page_banner_is_the_compact_variant(gated_client, published_questionnaire):
    response, _scores = _submit_all(gated_client, published_questionnaire)

    assert '<div class="profile-banner profile-banner--compact"' in response.content.decode()


def test_result_page_banner_is_decorative_and_carries_no_text_or_link(
    gated_client, published_questionnaire
):
    """Name und Link stehen auf der Seitenfläche, nicht auf den Farben (NFR-6)."""
    response, _scores = _submit_all(gated_client, published_questionnaire)

    banner = _banner(response.content.decode())
    assert 'aria-hidden="true"' in banner.split(">")[0]
    assert "<a " not in banner
    assert re.sub(r"<[^>]+>", "", banner).strip() == ""


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
