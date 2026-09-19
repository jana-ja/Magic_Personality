"""
Tests für die Farbwahl im Profil (Task 2.4, FR-P1, FR-P4; seit Task 4.5 nur noch
Farben — Nickname und Bio siehe apps/social/tests/test_profile_sections.py).
"""

import pytest

from apps.accounts.models import ColorAssignment, Profile, User
from apps.colors.models import ColorCombination
from apps.quiz.models import TestResult

pytestmark = pytest.mark.django_db

PROFILE_URL = "/accounts/profile/"  # Speichern (POST); die Seite selbst ist PROFILE_PAGE
PROFILE_PAGE = "/u/alex/"


@pytest.fixture
def user():
    user = User.objects.create_user(email="alex@example.com", password="a-long-enough-password")
    Profile.objects.create(user=user, nickname="alex", bio="Hi there.")
    return user


def _valid_data(**overrides):
    data = {"colors": []}
    data.update(overrides)
    return data


def test_profile_page_requires_login(gated_client):
    response = gated_client.get(PROFILE_PAGE)

    assert response.status_code == 302
    assert response.url.startswith("/accounts/login/")


def test_choosing_colors_creates_a_manual_color_assignment(gated_client, user):
    gated_client.force_login(user)

    gated_client.post(PROFILE_URL, _valid_data(colors=["W", "U"]))

    assignment = ColorAssignment.objects.get(profile=user.profile)
    assert assignment.combination.code == "WU"
    assert assignment.source == ColorAssignment.Source.SELF_MANUAL
    assert assignment.test_result is None


def test_choosing_no_colors_clears_an_existing_assignment(gated_client, user):
    combination = ColorCombination.objects.get(code="WU", locale="en")
    ColorAssignment.objects.create(
        profile=user.profile,
        author_profile=user.profile,
        combination=combination,
        source=ColorAssignment.Source.SELF_MANUAL,
    )
    gated_client.force_login(user)

    gated_client.post(PROFILE_URL, _valid_data(colors=[]))

    assert not ColorAssignment.objects.filter(profile=user.profile).exists()


def test_re_choosing_colors_overwrites_a_test_sourced_assignment(gated_client, user):
    """FR-P5/D-07: freie Auswahl setzt source = SELF_MANUAL und leert
    die Testreferenz, auch wenn zuvor ein Testergebnis übernommen war."""
    result = TestResult.objects.create(
        profile=user.profile,
        questionnaire_version=1,
        scores={"W": 5, "U": 3, "B": 4, "R": 4, "G": 4},
        result_colors="W",
    )
    combination_w = ColorCombination.objects.get(code="W", locale="en")
    ColorAssignment.objects.create(
        profile=user.profile,
        author_profile=user.profile,
        combination=combination_w,
        source=ColorAssignment.Source.SELF_TEST,
        test_result=result,
    )
    gated_client.force_login(user)

    gated_client.post(PROFILE_URL, _valid_data(colors=["U", "B"]))

    assignment = ColorAssignment.objects.get(profile=user.profile)
    assert assignment.combination.code == "UB"
    assert assignment.source == ColorAssignment.Source.SELF_MANUAL
    assert assignment.test_result is None


def _adopted_assignment(user, code="WU"):
    result = TestResult.objects.create(
        profile=user.profile,
        questionnaire_version=1,
        scores={"W": 9, "U": 10, "B": 6, "R": 2, "G": 3},
        result_colors=code,
    )
    assignment = ColorAssignment.objects.create(
        profile=user.profile,
        author_profile=user.profile,
        combination=ColorCombination.objects.get(code=code, locale="en"),
        source=ColorAssignment.Source.SELF_TEST,
        test_result=result,
    )
    return result, assignment


def test_saving_the_unchanged_colors_keeps_the_test_link(gated_client, user):
    """Regression (D-72): das Formular schickt die unveränderten Farben mit;
    das darf die Testreferenz nicht überschreiben (FR-P5)."""
    result, _ = _adopted_assignment(user)
    gated_client.force_login(user)

    gated_client.post(PROFILE_URL, _valid_data(colors=["W", "U"]))

    assignment = ColorAssignment.objects.get(profile=user.profile)
    assert assignment.source == ColorAssignment.Source.SELF_TEST
    assert assignment.test_result == result


def test_saving_the_same_colors_in_another_order_keeps_the_test_link(gated_client, user):
    result, _ = _adopted_assignment(user)
    gated_client.force_login(user)

    gated_client.post(PROFILE_URL, _valid_data(colors=["U", "W"]))

    assert ColorAssignment.objects.get(profile=user.profile).test_result == result


def test_actually_changing_the_colors_still_drops_the_test_link(gated_client, user):
    _adopted_assignment(user)
    gated_client.force_login(user)

    gated_client.post(PROFILE_URL, _valid_data(colors=["W", "U", "B"]))

    assignment = ColorAssignment.objects.get(profile=user.profile)
    assert assignment.combination.code == "WUB"
    assert assignment.source == ColorAssignment.Source.SELF_MANUAL
    assert assignment.test_result is None


def test_saving_no_colors_without_an_assignment_creates_nothing(gated_client, user):
    gated_client.force_login(user)

    gated_client.post(PROFILE_URL, _valid_data())

    assert not ColorAssignment.objects.filter(profile=user.profile).exists()
