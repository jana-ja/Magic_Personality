"""
Tests für Freundeslisten und Graph (Task 3.5, FR-S5, FR-S6).

Die drei Fälle aus der Definition of Done in docs/ROADMAP.md: eigene
Freundesliste im eigenen Profil, Freundesliste fremder Profile
einsehbar und navigierbar, über mindestens zwei Ebenen durchklickbar
ohne Sackgasse.
"""

import pytest

from apps.accounts.models import Profile, User
from apps.social import friendships

pytestmark = pytest.mark.django_db


@pytest.fixture
def alex():
    user = User.objects.create_user(email="alex@example.com", password="a-long-enough-password")
    return Profile.objects.create(user=user, nickname="alex")


@pytest.fixture
def jamie():
    user = User.objects.create_user(email="jamie@example.com", password="a-long-enough-password")
    return Profile.objects.create(user=user, nickname="jamie")


@pytest.fixture
def taylor():
    user = User.objects.create_user(email="taylor@example.com", password="a-long-enough-password")
    return Profile.objects.create(user=user, nickname="taylor")


def _befriend(profile_a, profile_b):
    friendship = friendships.send_request(profile_a, profile_b)
    friendships.accept_request(friendship, profile_b)


# apps.social.friendships.accepted_friends ----------------------------------


def test_accepted_friends_lists_the_other_side(alex, jamie):
    _befriend(alex, jamie)

    assert friendships.accepted_friends(alex) == [jamie]
    assert friendships.accepted_friends(jamie) == [alex]


def test_pending_requests_are_not_counted_as_friends(alex, jamie):
    friendships.send_request(alex, jamie)

    assert friendships.accepted_friends(alex) == []
    assert friendships.accepted_friends(jamie) == []


def test_accepted_friends_are_sorted_by_nickname(alex, jamie, taylor):
    _befriend(alex, jamie)
    _befriend(alex, taylor)

    assert friendships.accepted_friends(alex) == [jamie, taylor]


# FR-S5: eigene Freundesliste im eigenen Profil ------------------------------


def test_own_friends_list_is_visible_on_the_own_profile(gated_client, alex, jamie):
    _befriend(alex, jamie)
    gated_client.force_login(alex.user)

    response = gated_client.get("/u/alex/friends/")

    html = response.content.decode()
    assert 'href="/u/jamie/"' in html


def test_own_profile_without_friends_shows_a_neutral_message(gated_client, alex):
    gated_client.force_login(alex.user)

    response = gated_client.get("/u/alex/friends/")

    assert "No friends yet." in response.content.decode()


# FR-S6: Freundesliste fremder Profile einsehbar und navigierbar ------------


def test_foreign_profiles_friend_list_is_visible(gated_client, alex, jamie, taylor):
    _befriend(jamie, taylor)
    gated_client.force_login(alex.user)

    response = gated_client.get("/u/jamie/friends/")

    html = response.content.decode()
    assert 'href="/u/taylor/"' in html


def test_foreign_profile_without_friends_shows_a_neutral_message(gated_client, alex, jamie):
    gated_client.force_login(alex.user)

    response = gated_client.get("/u/jamie/friends/")

    assert "No friends yet." in response.content.decode()


def test_the_graph_is_navigable_across_at_least_two_levels_without_a_dead_end(
    gated_client, alex, jamie, taylor
):
    """
    Task 3.5-DoD: über mindestens zwei Ebenen durchklickbar, ohne
    Sackgasse. alex ist mit jamie befreundet, jamie mit taylor — von
    alex' eigenem Profil aus muss sich das bis zu taylor durchklicken
    lassen, und jede Station bietet selbst wieder eine (ggf. leere)
    Freundesliste, keine endet ohne Weiterkommen.
    """
    _befriend(alex, jamie)
    _befriend(jamie, taylor)
    gated_client.force_login(alex.user)

    # Ebene 0: eigenes Profil -> jamie.
    own_profile_html = gated_client.get("/u/alex/friends/").content.decode()
    assert 'href="/u/jamie/"' in own_profile_html

    # Ebene 1: jamies Profil -> alex (zurück) und taylor (weiter).
    jamie_html = gated_client.get("/u/jamie/friends/").content.decode()
    assert 'href="/u/alex/"' in jamie_html
    assert 'href="/u/taylor/"' in jamie_html

    # Ebene 2: taylors Profil -> jamie (zurück) — keine Sackgasse, die
    # Seite bietet immer eine (ggf. leere) Freundesliste an.
    taylor_html = gated_client.get("/u/taylor/friends/").content.decode()
    assert 'href="/u/jamie/"' in taylor_html
    assert "Friends" in taylor_html


def test_login_is_required_to_see_a_friend_list(gated_client, alex, jamie, taylor):
    _befriend(jamie, taylor)

    response = gated_client.get("/u/jamie/friends/")

    assert response.status_code == 302
    assert "/accounts/login/" in response.url
