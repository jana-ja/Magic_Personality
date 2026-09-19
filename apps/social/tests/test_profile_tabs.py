"""
Tests für die Tabs des Profils und den Freunde-Tab (Task 4.3, FR-P11,
FR-S5, FR-S6, D-73).
"""

import re

import pytest

from apps.accounts.models import Profile, User
from apps.social import friendships

pytestmark = pytest.mark.django_db


def _profile(nickname):
    user = User.objects.create_user(
        email=f"{nickname}@example.com", password="a-long-enough-password"
    )
    return Profile.objects.create(user=user, nickname=nickname)


@pytest.fixture
def alex():
    return _profile("alex")


@pytest.fixture
def jamie():
    return _profile("jamie")


@pytest.fixture
def taylor():
    return _profile("taylor")


def _befriend(a, b):
    friendships.accept_request(friendships.send_request(a, b), b)


def _get(client, viewer, path):
    client.force_login(viewer.user)
    return client.get(path).content.decode()


def _tabs(html):
    return re.search(r'<nav class="profile-tabs".*?</nav>', html, re.S).group(0)


def _current(html):
    return re.findall(r'<a href="([^"]+)" aria-current="page"', _tabs(html))


# Tab-Leiste -------------------------------------------------------------------


def test_the_tab_bar_links_to_pinboard_and_friends(gated_client, alex, jamie):
    tabs = _tabs(_get(gated_client, alex, "/u/jamie/"))

    assert 'href="/u/jamie/"' in tabs
    assert 'href="/u/jamie/friends/"' in tabs
    assert "Pinboard" in tabs
    assert "Friends" in tabs


def test_pinboard_is_the_default_tab_and_marked_current(gated_client, alex, jamie):
    html = _get(gated_client, alex, "/u/jamie/")

    assert _current(html) == ["/u/jamie/"]


def test_friends_tab_is_marked_current(gated_client, alex, jamie):
    html = _get(gated_client, alex, "/u/jamie/friends/")

    assert _current(html) == ["/u/jamie/friends/"]


def test_tabs_are_plain_links_without_javascript_hooks(gated_client, alex, jamie):
    tabs = _tabs(_get(gated_client, alex, "/u/jamie/"))

    assert "hx-" not in tabs
    assert "onclick" not in tabs
    assert 'role="tab"' not in tabs


def test_the_pinboard_shows_a_coming_soon_placeholder(gated_client, alex, jamie):
    html = _get(gated_client, alex, "/u/jamie/")

    assert "Coming soon" in html


def test_the_friends_tab_requires_login(gated_client, jamie):
    response = gated_client.get("/u/jamie/friends/")

    assert response.status_code == 302
    assert "/accounts/login/" in response.url


def test_an_unknown_nickname_is_a_404_on_the_friends_tab(gated_client, alex):
    gated_client.force_login(alex.user)

    assert gated_client.get("/u/nobody/friends/").status_code == 404


# Freunde-Tab ------------------------------------------------------------------


def test_the_friends_tab_lists_all_friends_of_that_profile(gated_client, alex, jamie, taylor):
    _befriend(jamie, taylor)
    _befriend(jamie, alex)

    html = _get(gated_client, alex, "/u/jamie/friends/")

    assert 'href="/u/taylor/"' in html
    assert 'href="/u/alex/"' in html


def test_the_pinboard_tab_shows_only_a_preview_of_the_friends(gated_client, alex, jamie, taylor):
    """Die Sidebar zeigt höchstens acht (Task 4.7); die vollständige Liste steht im Tab Friends."""
    _befriend(jamie, taylor)

    html = _get(gated_client, alex, "/u/jamie/")

    assert 'href="/u/taylor/"' in html
    assert 'href="/u/jamie/friends/"' in html


def test_the_friends_tab_says_so_when_there_are_no_friends(gated_client, alex, jamie):
    html = _get(gated_client, alex, "/u/jamie/friends/")

    assert "No friends yet." in html


def test_the_graph_stays_navigable_through_the_friends_tab(gated_client, alex, jamie, taylor):
    _befriend(alex, jamie)
    _befriend(jamie, taylor)

    own = _get(gated_client, alex, "/u/alex/friends/")
    assert 'href="/u/jamie/"' in own
    level_one = _get(gated_client, alex, "/u/jamie/friends/")
    assert 'href="/u/taylor/"' in level_one
    level_two = _get(gated_client, alex, "/u/taylor/friends/")
    assert 'href="/u/jamie/"' in level_two


# Offene Anfragen: nur eigene Person ------------------------------------------------


def test_own_friends_tab_lists_received_and_sent_requests(gated_client, alex, jamie, taylor):
    received = friendships.send_request(jamie, alex)
    sent = friendships.send_request(alex, taylor)

    html = _get(gated_client, alex, "/u/alex/friends/")

    assert f'action="/friends/{received.pk}/accept/"' in html
    assert f'action="/friends/{received.pk}/decline/"' in html
    assert f'action="/friends/{sent.pk}/decline/"' in html
    assert "Cancel request" in html


def test_own_friends_tab_says_so_when_there_are_no_open_requests(gated_client, alex):
    html = _get(gated_client, alex, "/u/alex/friends/")

    assert "No open friend requests." in html


def test_the_requests_box_is_gone_from_the_pinboard_tab(gated_client, alex, jamie):
    friendships.send_request(jamie, alex)

    html = _get(gated_client, alex, "/u/alex/")

    assert "Friend requests" not in html
    assert "/accept/" not in html


def test_the_tab_shows_the_number_of_open_requests(gated_client, alex, jamie, taylor):
    friendships.send_request(jamie, alex)
    friendships.send_request(taylor, alex)

    tabs = _tabs(_get(gated_client, alex, "/u/alex/"))

    assert 'class="profile-tabs__count" aria-hidden="true">2<' in tabs
    assert "2 open requests" in tabs


def test_the_tab_has_no_counter_without_open_requests(gated_client, alex):
    tabs = _tabs(_get(gated_client, alex, "/u/alex/"))

    assert "profile-tabs__count" not in tabs


def test_sent_requests_are_not_counted_as_new(gated_client, alex, jamie):
    friendships.send_request(alex, jamie)

    tabs = _tabs(_get(gated_client, alex, "/u/alex/"))

    assert "profile-tabs__count" not in tabs


def test_open_requests_of_others_appear_nowhere_in_a_foreign_profile(
    gated_client, alex, jamie, taylor
):
    """jamies offene Anfragen (empfangen wie gesendet) sind für alex auf
    keinem Tab von jamies Profil zu sehen."""
    friendships.send_request(taylor, jamie)
    friendships.send_request(jamie, alex)
    gated_client.force_login(alex.user)

    for path in ("/u/jamie/", "/u/jamie/friends/"):
        html = gated_client.get(path).content.decode()
        assert "Friend requests" not in html, path
        assert 'href="/u/taylor/"' not in html, path
        assert "profile-tabs__count" not in _tabs(html), path
