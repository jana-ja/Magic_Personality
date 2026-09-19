"""
Tests für die Autorenkarte (Task 4.8, FR-P15, D-57, D-73): Profilbild,
Nickname und Kombination als Chip, wiederverwendbar mit nur einem Profil.
"""

import re

import pytest
from django.db import connection
from django.template import Context, Template
from django.test.utils import CaptureQueriesContext

from apps.accounts.models import ColorAssignment, Profile, User
from apps.colors.models import ColorCombination
from apps.social import friendships

pytestmark = pytest.mark.django_db


def _profile(nickname):
    user = User.objects.create_user(
        email=f"{nickname}@example.com", password="a-long-enough-password"
    )
    return Profile.objects.create(user=user, nickname=nickname)


def _assign(profile, code):
    ColorAssignment.objects.create(
        profile=profile,
        author_profile=profile,
        combination=ColorCombination.objects.get(code=code, locale="en"),
        source=ColorAssignment.Source.SELF_MANUAL,
    )


def _befriend(a, b):
    friendships.accept_request(friendships.send_request(a, b), b)


@pytest.fixture
def alex():
    return _profile("alex")


@pytest.fixture
def jamie():
    return _profile("jamie")


def _render(profile, size=None):
    argument = f' size="{size}"' if size else ""
    template = Template("{% load social_tags %}{% author_card profile" + argument + " %}")
    return template.render(Context({"profile": profile}))


# Baustein ----------------------------------------------------------------------------------------


def test_the_card_shows_avatar_nickname_link_and_combination_chip(jamie):
    ColorCombination.objects.filter(code="UB", locale="en").update(name="Dimir")
    _assign(jamie, "UB")

    html = _render(jamie)

    assert 'class="avatar"' in html
    assert 'class="author-card__name" href="/u/jamie/">jamie</a>' in html
    assert '<span class="author-card__chip">Dimir</span>' in html
    assert html.count("avatar__segment") == 2


def test_the_card_without_colors_has_a_neutral_avatar_and_no_chip(jamie):
    html = _render(jamie)

    assert "avatar__segment--neutral" in html
    assert "author-card__chip" not in html
    assert 'href="/u/jamie/"' in html


def test_the_card_needs_nothing_but_a_profile(jamie):
    """Wie es Beiträge und Kommentare später aufrufen: nur ein Profil, keine
    Sonderfälle je Einsatzort (Task 4.8-DoD)."""
    template = Template("{% load social_tags %}{% author_card comment.author %}")

    html = template.render(Context({"comment": type("Comment", (), {"author": jamie})()}))

    assert 'href="/u/jamie/"' in html


@pytest.mark.parametrize("size", ["small", "medium"])
def test_both_sizes_render(jamie, size):
    assert f"author-card--{size}" in _render(jamie, size)


def test_medium_is_the_default_size(jamie):
    assert "author-card--medium" in _render(jamie)


def test_an_unknown_size_is_rejected(jamie):
    with pytest.raises(ValueError):
        _render(jamie, "huge")


def test_the_avatar_is_decorative_next_to_the_name(jamie):
    html = _render(jamie)

    assert re.search(r'class="author-card__avatar" aria-hidden="true"', html)


def test_the_nickname_is_escaped(gated_client):
    profile = Profile.objects.create(nickname="<i>x")

    html = _render(profile)

    assert "<i>x" not in html
    assert "&lt;i&gt;x" in html


def test_many_cards_on_one_page_produce_no_duplicate_ids(jamie):
    _assign(jamie, "UB")

    html = "".join(_render(jamie, "small") for _ in range(5))

    assert 'id="' not in html


# Einsatz: Listen und Suchen ---------------------------------------------------------------


def test_the_friends_tab_uses_the_card(gated_client, alex, jamie):
    _assign(jamie, "UB")
    _befriend(alex, jamie)
    gated_client.force_login(alex.user)

    html = gated_client.get("/u/alex/friends/").content.decode()

    assert 'class="author-card__name" href="/u/jamie/"' in html
    assert "author-card--medium" in html
    assert "author-card__chip" in html


def test_the_friends_preview_in_the_sidebar_uses_the_small_card(gated_client, alex, jamie):
    _befriend(alex, jamie)
    gated_client.force_login(alex.user)

    html = gated_client.get("/u/alex/").content.decode()

    assert "author-card--small" in html
    assert 'class="author-card__name" href="/u/jamie/"' in html


def test_open_requests_use_the_small_card(gated_client, alex, jamie):
    friendships.send_request(jamie, alex)
    taylor = _profile("taylor")
    friendships.send_request(alex, taylor)
    gated_client.force_login(alex.user)

    html = gated_client.get("/u/alex/friends/").content.decode()

    assert 'class="author-card__name" href="/u/jamie/"' in html
    assert 'class="author-card__name" href="/u/taylor/"' in html


def test_the_nickname_search_shows_cards(gated_client, alex, jamie):
    _assign(jamie, "UB")
    gated_client.force_login(alex.user)

    html = gated_client.get("/search/?q=jam").content.decode()

    assert 'class="author-card__name" href="/u/jamie/"' in html
    assert "author-card__chip" in html


def test_the_color_search_shows_cards(gated_client, alex, jamie):
    _assign(jamie, "UB")
    gated_client.force_login(alex.user)

    html = gated_client.get("/search/colors/u/").content.decode()

    assert 'class="author-card__name" href="/u/jamie/"' in html


def test_a_page_full_of_cards_has_no_duplicate_ids(gated_client, alex):
    for index in range(6):
        friend = _profile(f"friend{index}")
        _assign(friend, "UB")
        _befriend(alex, friend)
    gated_client.force_login(alex.user)

    html = gated_client.get("/u/alex/friends/").content.decode()
    ids = re.findall(r'\sid="([^"]+)"', html)

    assert len(ids) == len(set(ids))


def test_lists_of_cards_do_not_query_per_profile(gated_client, alex):
    """Zuordnung und Kombination kommen per Prefetch, die Farbwerte einmal je
    Rendering: mehr Karten kosten keine zusätzlichen Abfragen."""
    gated_client.force_login(alex.user)

    def count_queries(friends):
        for index in range(friends):
            friend = _profile(f"bulk{friends}_{index}")
            _assign(friend, "UB")
            _befriend(alex, friend)
        with CaptureQueriesContext(connection) as queries:
            gated_client.get("/u/alex/friends/")
        return len(queries)

    few = count_queries(2)
    many = count_queries(6)

    assert many == few
