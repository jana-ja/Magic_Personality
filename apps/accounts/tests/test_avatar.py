"""
Tests für das generierte Profilbild (Task 2.5, FR-P3, D-13).

Deckt die Definition of Done wörtlich ab: deterministisch aus den
hinterlegten Farben, kein Upload/keine Dateiablage (reine Funktionen,
kein `ImageField`/`FileField` beteiligt), neutrale Darstellung ohne
Farben.
"""

import pytest

from apps.accounts import avatar
from apps.accounts.models import ColorAssignment, Profile, User
from apps.colors.models import Color, ColorCombination

pytestmark = pytest.mark.django_db

PROFILE_URL = "/accounts/profile/"  # Speichern (POST); die Seite selbst ist PROFILE_PAGE
PROFILE_PAGE = "/u/alex/"


def test_no_colors_yields_no_segments():
    assert avatar.segments([]) == []


def test_one_color_yields_one_full_width_segment():
    white_hex = Color.objects.get(code="W").hex

    result = avatar.segments(["W"])

    assert result == [avatar.Segment(x=0, width=100, hex=white_hex)]


def test_two_colors_yield_two_equal_segments_in_the_given_order():
    white_hex = Color.objects.get(code="W").hex
    blue_hex = Color.objects.get(code="U").hex

    result = avatar.segments(["W", "U"])

    assert result == [
        avatar.Segment(x=0, width=50, hex=white_hex),
        avatar.Segment(x=50, width=50, hex=blue_hex),
    ]


def test_five_colors_yield_five_equal_segments():
    result = avatar.segments(["W", "U", "B", "R", "G"])

    assert len(result) == 5
    assert all(segment.width == pytest.approx(20) for segment in result)
    assert [segment.x for segment in result] == pytest.approx([0, 20, 40, 60, 80])


def test_generation_is_deterministic_across_calls():
    assert avatar.segments(["W", "U", "B"]) == avatar.segments(["W", "U", "B"])


def test_avatar_context_without_a_color_assignment_has_no_segments():
    context = avatar.avatar_context(None)

    assert context["segments"] == []


def test_avatar_context_derives_segments_from_the_combination():
    profile = Profile.objects.create(nickname="alex")
    combination = ColorCombination.objects.get(code="WU", locale="en")
    assignment = ColorAssignment.objects.create(
        profile=profile,
        author_profile=profile,
        combination=combination,
        source=ColorAssignment.Source.SELF_MANUAL,
    )

    context = avatar.avatar_context(assignment)

    assert [segment.hex for segment in context["segments"]] == [
        Color.objects.get(code="W").hex,
        Color.objects.get(code="U").hex,
    ]


# Auf der Profilseite gerendert (Task 2.4) -----------------------------


@pytest.fixture
def user():
    user = User.objects.create_user(email="alex@example.com", password="a-long-enough-password")
    Profile.objects.create(user=user, nickname="alex")
    return user


def test_profile_without_colors_renders_a_neutral_avatar(gated_client, user):
    gated_client.force_login(user)

    response = gated_client.get(PROFILE_PAGE)

    html = response.content.decode()
    assert 'class="avatar__segment avatar__segment--neutral"' in html
    assert "--segment-color" not in html


def test_profile_with_colors_renders_the_matching_segments(gated_client, user):
    combination = ColorCombination.objects.get(code="WU", locale="en")
    ColorAssignment.objects.create(
        profile=user.profile,
        author_profile=user.profile,
        combination=combination,
        source=ColorAssignment.Source.SELF_MANUAL,
    )
    gated_client.force_login(user)

    response = gated_client.get(PROFILE_PAGE)

    html = response.content.decode()
    assert Color.objects.get(code="W").hex in html
    assert Color.objects.get(code="U").hex in html
    assert "avatar__segment--neutral" not in html
