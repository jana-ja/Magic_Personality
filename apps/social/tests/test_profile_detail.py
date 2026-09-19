"""
Tests für fremde Profile (Task 3.1, FR-S1).

Die beiden Fälle aus der Definition of Done in docs/ROADMAP.md stehen
wörtlich drin: nicht angemeldete Nutzende werden abgewiesen, und die
Testhistorie taucht in keiner Antwort auf.
"""

import pytest

from apps.accounts.models import ColorAssignment, Profile, User
from apps.colors.models import ColorCombination
from apps.quiz.models import TestResult

pytestmark = pytest.mark.django_db


@pytest.fixture
def user():
    user = User.objects.create_user(email="alex@example.com", password="a-long-enough-password")
    Profile.objects.create(user=user, nickname="alex")
    return user


@pytest.fixture
def other_user():
    user = User.objects.create_user(email="jamie@example.com", password="a-long-enough-password")
    Profile.objects.create(user=user, nickname="jamie", bio="Draft player.")
    return user


def _assign_colors(profile, code="WU"):
    combination = ColorCombination.objects.get(code=code, locale="en")
    return ColorAssignment.objects.create(
        profile=profile,
        author_profile=profile,
        combination=combination,
        source=ColorAssignment.Source.SELF_MANUAL,
    )


# FR-S1: nur für Angemeldete erreichbar ---------------------------------


def test_anonymous_visitor_is_redirected_to_login(gated_client, other_user):
    response = gated_client.get("/u/jamie/")

    assert response.status_code == 302
    assert "/accounts/login/" in response.url


def test_logged_in_visitor_sees_the_foreign_profile(gated_client, user, other_user):
    _assign_colors(other_user.profile)
    gated_client.force_login(user)

    response = gated_client.get("/u/jamie/")

    assert response.status_code == 200
    html = response.content.decode()
    assert "jamie" in html
    assert "Draft player." in html
    assert 'href="/colors/wu/"' in html


def test_nickname_lookup_is_case_insensitive(gated_client, user, other_user):
    gated_client.force_login(user)

    response = gated_client.get("/u/Jamie/")

    assert response.status_code == 200


def test_unknown_nickname_is_404(gated_client, user):
    gated_client.force_login(user)

    response = gated_client.get("/u/nobody-here/")

    assert response.status_code == 404


# FR-S1: nicht Testhistorie, nicht E-Mail --------------------------------


def test_foreign_profile_never_shows_test_history_or_email(gated_client, user, other_user):
    TestResult.objects.create(
        profile=other_user.profile,
        questionnaire_version=1,
        scores={"W": 5, "U": 3, "B": 0, "R": 0, "G": 0},
        result_colors="WU",
    )
    gated_client.force_login(user)

    response = gated_client.get("/u/jamie/")

    html = response.content.decode()
    assert other_user.email not in html
    assert "delete" not in html.lower()


def test_profile_without_colors_shows_a_neutral_message(gated_client, user, other_user):
    gated_client.force_login(user)

    response = gated_client.get("/u/jamie/")

    html = response.content.decode()
    assert "No colors set yet." in html


# D-70: Punkteverteilung des übernommenen Testergebnisses -----------------


def _adopt_test_result(profile, scores):
    result = TestResult.objects.create(
        profile=profile, questionnaire_version=1, scores=scores, result_colors="WU"
    )
    assignment = _assign_colors(profile)
    assignment.source = ColorAssignment.Source.SELF_TEST
    assignment.test_result = result
    assignment.save()
    return result


def test_foreign_profile_shows_the_scores_of_the_adopted_test_result(
    gated_client, user, other_user
):
    _adopt_test_result(other_user.profile, {"W": 9, "U": 10, "B": 6, "R": 2, "G": 3})
    gated_client.force_login(user)

    html = gated_client.get("/u/jamie/").content.decode()

    assert "W: 9, U: 10, B: 6, R: 2, G: 3" in html


def test_foreign_profile_shows_no_scores_for_manually_chosen_colors(gated_client, user, other_user):
    _assign_colors(other_user.profile)
    gated_client.force_login(user)

    html = gated_client.get("/u/jamie/").content.decode()

    assert "Points from the test result" not in html


def test_foreign_profile_shows_no_scores_once_the_result_was_deleted(
    gated_client, user, other_user
):
    """FR-P8: das Löschen leert die Referenz, die Farben bleiben."""
    result = _adopt_test_result(other_user.profile, {"W": 9, "U": 10, "B": 6, "R": 2, "G": 3})
    result.delete()
    gated_client.force_login(user)

    html = gated_client.get("/u/jamie/").content.decode()

    assert 'href="/colors/wu/"' in html
    assert "Points from the test result" not in html


def test_other_results_of_the_history_stay_private(gated_client, user, other_user):
    _adopt_test_result(other_user.profile, {"W": 9, "U": 10, "B": 6, "R": 2, "G": 3})
    TestResult.objects.create(
        profile=other_user.profile,
        questionnaire_version=1,
        scores={"W": 1, "U": 2, "B": 3, "R": 4, "G": 5},
        result_colors="RG",
    )
    gated_client.force_login(user)

    html = gated_client.get("/u/jamie/").content.decode()

    assert "W: 1, U: 2, B: 3, R: 4, G: 5" not in html
