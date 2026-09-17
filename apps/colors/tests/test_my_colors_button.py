"""
Tests für den „Meine Farben auswählen"-Button (Task 2.13, FR-C12).
"""

import pytest

from apps.accounts.models import ColorAssignment, Profile, User
from apps.colors.models import ColorCombination

pytestmark = pytest.mark.django_db

BUTTON_TEXT = "Select my colors"


@pytest.fixture
def user():
    user = User.objects.create_user(email="alex@example.com", password="a-long-enough-password")
    Profile.objects.create(user=user, nickname="alex")
    return user


def test_button_is_absent_for_anonymous_visitors(gated_client):
    response = gated_client.get("/colors/")

    assert BUTTON_TEXT not in response.content.decode()


def test_button_is_absent_for_a_logged_in_user_without_colors(gated_client, user):
    gated_client.force_login(user)

    response = gated_client.get("/colors/")

    assert BUTTON_TEXT not in response.content.decode()


def test_button_appears_and_links_to_the_own_combination(gated_client, user):
    combination = ColorCombination.objects.get(code="WU", locale="en")
    ColorAssignment.objects.create(
        profile=user.profile,
        author_profile=user.profile,
        combination=combination,
        source=ColorAssignment.Source.SELF_MANUAL,
    )
    gated_client.force_login(user)

    response = gated_client.get("/colors/")

    html = response.content.decode()
    assert BUTTON_TEXT in html
    assert 'href="/colors/wu/"' in html


def test_button_still_appears_on_a_different_selection(gated_client, user):
    """Der Button bleibt sichtbar, egal welche Farben gerade selektiert
    sind — er zeigt immer auf die eigenen, hinterlegten Farben."""
    combination = ColorCombination.objects.get(code="WU", locale="en")
    ColorAssignment.objects.create(
        profile=user.profile,
        author_profile=user.profile,
        combination=combination,
        source=ColorAssignment.Source.SELF_MANUAL,
    )
    gated_client.force_login(user)

    response = gated_client.get("/colors/b/")

    html = response.content.decode()
    assert BUTTON_TEXT in html
    assert 'href="/colors/wu/"' in html


def test_button_is_htmx_accelerated_like_the_reset_link(gated_client, user):
    combination = ColorCombination.objects.get(code="W", locale="en")
    ColorAssignment.objects.create(
        profile=user.profile,
        author_profile=user.profile,
        combination=combination,
        source=ColorAssignment.Source.SELF_MANUAL,
    )
    gated_client.force_login(user)

    response = gated_client.get("/colors/")

    html = response.content.decode()
    assert 'hx-get="/colors/w/"' in html
    assert 'hx-target="#colors-panel"' in html
