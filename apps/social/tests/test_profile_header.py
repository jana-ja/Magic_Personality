"""
Tests für den Kopfbereich der Profilseite (Task 4.2, FR-P10, D-73).
"""

import re

import pytest

from apps.accounts.models import ColorAssignment, Profile, User
from apps.colors.models import Color, ColorCombination
from apps.social import friendships

pytestmark = pytest.mark.django_db


@pytest.fixture
def alex():
    user = User.objects.create_user(email="alex@example.com", password="a-long-enough-password")
    return Profile.objects.create(user=user, nickname="alex", bio="Alex bio.")


@pytest.fixture
def jamie():
    user = User.objects.create_user(email="jamie@example.com", password="a-long-enough-password")
    return Profile.objects.create(user=user, nickname="jamie", bio="Jamie bio.")


def _assign(profile, code):
    return ColorAssignment.objects.create(
        profile=profile,
        author_profile=profile,
        combination=ColorCombination.objects.get(code=code, locale="en"),
        source=ColorAssignment.Source.SELF_MANUAL,
    )


def _header(html):
    return re.search(r'<header class="profile-head">.*?</header>', html, re.S).group(0)


def _banner(html):
    return re.search(r'<div class="profile-banner".*?</div>', html, re.S).group(0)


def _view(client, viewer, nickname):
    client.force_login(viewer.user)
    return client.get(f"/u/{nickname}/").content.decode()


# Banner -------------------------------------------------------------------


@pytest.mark.parametrize("code", ["W", "UB", "WBG", "WUBR", "WUBRG"])
def test_banner_has_one_stripe_per_color_in_wubrg_order(gated_client, alex, jamie, code):
    _assign(jamie, code)
    hex_by_code = dict(Color.objects.values_list("code", "hex"))

    banner = _banner(_view(gated_client, alex, "jamie"))

    hexes = re.findall(r"--segment-color: (#[0-9A-Fa-f]{6})", banner)
    assert hexes == [hex_by_code[letter] for letter in code]
    assert "profile-banner__stripe--neutral" not in banner


def test_profile_without_colors_gets_a_neutral_banner(gated_client, alex, jamie):
    banner = _banner(_view(gated_client, alex, "jamie"))

    assert "profile-banner__stripe--neutral" in banner
    assert "--segment-color" not in banner


def test_banner_is_decorative_for_screen_readers(gated_client, alex, jamie):
    _assign(jamie, "UB")

    banner = _banner(_view(gated_client, alex, "jamie"))

    assert 'aria-hidden="true"' in banner


# Text steht nie auf dem Banner ---------------------------------------------------


def test_no_text_is_placed_inside_the_banner(gated_client, alex, jamie):
    _assign(jamie, "UB")

    banner = _banner(_view(gated_client, alex, "jamie"))

    assert re.sub(r"<[^>]+>", "", banner).strip() == ""


# Name, Kombination, Bio ---------------------------------------------------------


def test_header_shows_name_combination_link_and_bio(gated_client, alex, jamie):
    _assign(jamie, "UB")

    header = _header(_view(gated_client, alex, "jamie"))

    assert "<h1" in header and "jamie" in header
    assert 'href="/colors/ub/"' in header
    assert "Jamie bio." in header


def test_a_long_bio_is_shortened_in_the_header(gated_client, alex, jamie):
    jamie.bio = "x" * 300
    jamie.save()

    header = _header(_view(gated_client, alex, "jamie"))

    assert "x" * 300 not in header
    assert "…" in header


def test_header_without_combination_or_bio_renders(gated_client, alex, jamie):
    jamie.bio = ""
    jamie.save()

    header = _header(_view(gated_client, alex, "jamie"))

    assert "profile-head__combination" not in header
    assert "profile-head__bio" not in header


# Freundschaftsaktion im Kopf ------------------------------------------------------


def test_header_offers_to_send_a_request_when_there_is_no_relationship(gated_client, alex, jamie):
    header = _header(_view(gated_client, alex, "jamie"))

    assert 'action="/u/jamie/friend-request/"' in header
    assert "Send friend request" in header


def test_header_offers_to_cancel_a_sent_request(gated_client, alex, jamie):
    friendship = friendships.send_request(alex, jamie)

    header = _header(_view(gated_client, alex, "jamie"))

    assert "Friend request sent." in header
    assert f'action="/friends/{friendship.pk}/decline/"' in header


def test_header_offers_accept_and_decline_for_a_received_request(gated_client, alex, jamie):
    friendship = friendships.send_request(jamie, alex)

    header = _header(_view(gated_client, alex, "jamie"))

    assert f'action="/friends/{friendship.pk}/accept/"' in header
    assert f'action="/friends/{friendship.pk}/decline/"' in header


def test_header_offers_to_remove_a_friend(gated_client, alex, jamie):
    friendship = friendships.send_request(alex, jamie)
    friendships.accept_request(friendship, jamie)

    header = _header(_view(gated_client, alex, "jamie"))

    assert "You are friends." in header
    assert f'action="/friends/{friendship.pk}/remove/"' in header


def test_the_friend_action_is_only_in_the_header(gated_client, alex, jamie):
    html = _view(gated_client, alex, "jamie")

    assert html.count('action="/u/jamie/friend-request/"') == 1


# Eigene Person --------------------------------------------------------------------


def test_own_header_shows_a_you_hint_instead_of_a_friend_action(gated_client, alex):
    header = _header(_view(gated_client, alex, "alex"))

    assert "you" in header
    assert "friend-request" not in header
    assert "Send friend request" not in header
