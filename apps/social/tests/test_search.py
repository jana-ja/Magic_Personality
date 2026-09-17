"""
Tests für die Nickname-Suche (Task 3.2, FR-S2).

Teilstring-Suche, Groß-/Kleinschreibung egal, Treffer verlinken auf
das Profil.
"""

import pytest

from apps.accounts.models import Profile, User

pytestmark = pytest.mark.django_db


@pytest.fixture
def user():
    user = User.objects.create_user(email="alex@example.com", password="a-long-enough-password")
    Profile.objects.create(user=user, nickname="alex")
    return user


@pytest.fixture
def other_profiles():
    Profile.objects.create(nickname="Jamie")
    Profile.objects.create(nickname="jamison")
    Profile.objects.create(nickname="taylor")
    return None


def test_anonymous_visitor_is_redirected_to_login(gated_client):
    response = gated_client.get("/search/?q=jam")

    assert response.status_code == 302
    assert "/accounts/login/" in response.url


def test_substring_search_is_case_insensitive(gated_client, user, other_profiles):
    gated_client.force_login(user)

    response = gated_client.get("/search/?q=JAM")

    html = response.content.decode()
    assert 'href="/u/Jamie/"' in html
    assert 'href="/u/jamison/"' in html
    assert "taylor" not in html


def test_search_result_links_to_the_profile(gated_client, user, other_profiles):
    gated_client.force_login(user)

    response = gated_client.get("/search/?q=taylor")

    html = response.content.decode()
    assert 'href="/u/taylor/"' in html


def test_no_matches_shows_a_message_instead_of_an_error(gated_client, user, other_profiles):
    gated_client.force_login(user)

    response = gated_client.get("/search/?q=nobody-matches-this")

    assert response.status_code == 200
    assert "No profiles found." in response.content.decode()


def test_empty_query_shows_no_results(gated_client, user, other_profiles):
    gated_client.force_login(user)

    response = gated_client.get("/search/")

    html = response.content.decode()
    assert "Jamie" not in html
    assert "No profiles found." not in html
