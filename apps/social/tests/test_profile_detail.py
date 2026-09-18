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


# Das eigene Profil zeigt sich nicht wie ein fremdes -------------------------


def test_visiting_ones_own_profile_by_nickname_redirects_to_the_profile_page(gated_client, user):
    """
    Sonst erschiene das eigene Profil wie ein fremdes, inklusive eines
    "Anfrage senden"-Knopfs, der an der Selbstfreundschafts-Sperre in
    apps.social.friendships.send_request ohnehin nur mit einem Fehler
    enden würde.
    """
    gated_client.force_login(user)

    response = gated_client.get("/u/alex/")

    assert response.status_code == 302
    assert response.url == "/accounts/profile/"
