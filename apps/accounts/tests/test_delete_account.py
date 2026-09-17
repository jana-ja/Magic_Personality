"""
Tests für die Account-Löschung (Task 2.3, FR-U8).

Der wichtigste Fall ist wörtlich aus der Definition of Done in
docs/ROADMAP.md: nach der Löschung existiert keine Zeile mehr, die auf
den Account verweist. Profil, Farbzuordnung und Testhistorie hängen
über `on_delete=CASCADE` an `User`/`Profile` (Task 2.1/2.6, D-22) —
dieser Test belegt, dass diese Kaskade tatsächlich bis zum Ende
durchgreift, nicht nur die View selbst.
"""

import pytest

from apps.accounts.models import ColorAssignment, Profile, User
from apps.colors.models import ColorCombination
from apps.quiz.models import TestResult

pytestmark = pytest.mark.django_db

DELETE_URL = "/accounts/delete/"


@pytest.fixture
def user():
    user = User.objects.create_user(email="alex@example.com", password="a-long-enough-password")
    Profile.objects.create(user=user, nickname="alex")
    return user


def test_delete_account_requires_login(gated_client):
    response = gated_client.get(DELETE_URL)

    assert response.status_code == 302
    assert response.url.startswith("/accounts/login/")


def test_confirmation_page_is_reachable_when_logged_in(gated_client, user):
    gated_client.force_login(user)

    response = gated_client.get(DELETE_URL)

    assert response.status_code == 200
    assert "permanently delete" in response.content.decode().lower()


def test_get_does_not_delete_the_account(gated_client, user):
    gated_client.force_login(user)

    gated_client.get(DELETE_URL)

    assert User.objects.filter(pk=user.pk).exists()


def test_post_deletes_the_user_and_the_profile(gated_client, user):
    profile = user.profile
    gated_client.force_login(user)

    gated_client.post(DELETE_URL)

    assert not User.objects.filter(pk=user.pk).exists()
    assert not Profile.objects.filter(pk=profile.pk).exists()


def test_post_deletes_the_color_assignment(gated_client, user):
    profile = user.profile
    combination = ColorCombination.objects.get(code="WU", locale="en")
    assignment = ColorAssignment.objects.create(
        profile=profile,
        author_profile=profile,
        combination=combination,
        source=ColorAssignment.Source.SELF_MANUAL,
    )
    gated_client.force_login(user)

    gated_client.post(DELETE_URL)

    assert not ColorAssignment.objects.filter(pk=assignment.pk).exists()


def test_post_deletes_the_test_history(gated_client, user):
    profile = user.profile
    result = TestResult.objects.create(
        profile=profile,
        questionnaire_version=1,
        scores={"W": 5, "U": 3, "B": 4, "R": 4, "G": 4},
        result_colors="WU",
    )
    gated_client.force_login(user)

    gated_client.post(DELETE_URL)

    assert not TestResult.objects.filter(pk=result.pk).exists()


def test_post_ends_the_session(gated_client, user):
    gated_client.force_login(user)

    response = gated_client.post(DELETE_URL, follow=True)

    assert not response.wsgi_request.user.is_authenticated


def test_post_redirects_to_the_homepage(gated_client, user):
    gated_client.force_login(user)

    response = gated_client.post(DELETE_URL)

    assert response.status_code == 302
    assert response.url == "/colors/"
