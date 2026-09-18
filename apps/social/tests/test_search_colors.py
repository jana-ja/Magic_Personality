"""
Tests für die Suche nach Farbkombination (Task 3.3, FR-S3, D-21).

Der Fall aus der Definition of Done in docs/ROADMAP.md steht wörtlich
drin: Suche "W" findet WU und WB; Suche "WU" findet WUB, aber nicht WB.
"""

import pytest

from apps.accounts.models import ColorAssignment, Profile, User
from apps.colors.models import ColorCombination

pytestmark = pytest.mark.django_db


@pytest.fixture
def user():
    user = User.objects.create_user(email="alex@example.com", password="a-long-enough-password")
    Profile.objects.create(user=user, nickname="alex")
    return user


def _profile_with_colors(nickname, code):
    profile = Profile.objects.create(nickname=nickname)
    combination = ColorCombination.objects.get(code=code, locale="en")
    ColorAssignment.objects.create(
        profile=profile,
        author_profile=profile,
        combination=combination,
        source=ColorAssignment.Source.SELF_MANUAL,
    )
    return profile


def test_anonymous_visitor_is_redirected_to_login(gated_client):
    response = gated_client.get("/search/colors/w/")

    assert response.status_code == 302
    assert "/accounts/login/" in response.url


def test_searching_white_finds_wu_and_wb_but_not_a_profile_without_white(gated_client, user):
    _profile_with_colors("wu-profile", "WU")
    _profile_with_colors("wb-profile", "WB")
    _profile_with_colors("ub-profile", "UB")
    gated_client.force_login(user)

    response = gated_client.get("/search/colors/w/")

    html = response.content.decode()
    assert 'href="/u/wu-profile/"' in html
    assert 'href="/u/wb-profile/"' in html
    assert "ub-profile" not in html


def test_searching_wu_finds_wub_but_not_wb(gated_client, user):
    """Aus der DoD wörtlich: Suche "WU" findet WUB, aber nicht WB."""
    _profile_with_colors("wub-profile", "WUB")
    _profile_with_colors("wb-profile", "WB")
    gated_client.force_login(user)

    response = gated_client.get("/search/colors/wu/")

    html = response.content.decode()
    assert 'href="/u/wub-profile/"' in html
    assert "wb-profile" not in html


def test_exact_match_is_found_too(gated_client, user):
    _profile_with_colors("wu-profile", "WU")
    gated_client.force_login(user)

    response = gated_client.get("/search/colors/wu/")

    assert 'href="/u/wu-profile/"' in response.content.decode()


def test_no_matches_shows_a_message_instead_of_an_error(gated_client, user):
    gated_client.force_login(user)

    response = gated_client.get("/search/colors/g/")

    assert response.status_code == 200
    assert "No profiles found." in response.content.decode()


def test_empty_selection_shows_no_results(gated_client, user):
    _profile_with_colors("wu-profile", "WU")
    gated_client.force_login(user)

    response = gated_client.get("/search/colors/")

    html = response.content.decode()
    assert "wu-profile" not in html
    assert "No profiles found." not in html


def test_invalid_code_is_404(gated_client, user):
    gated_client.force_login(user)

    response = gated_client.get("/search/colors/x/")

    assert response.status_code == 404


def test_non_canonical_code_redirects_permanently(gated_client, user):
    gated_client.force_login(user)

    response = gated_client.get("/search/colors/uw/")

    assert response.status_code == 301
    assert response.url == "/search/colors/wu/"


def test_selection_uses_the_same_pentagon_markup_as_the_color_wheel(gated_client, user):
    gated_client.force_login(user)

    response = gated_client.get("/search/colors/")

    html = response.content.decode()
    assert 'class="pentagon"' in html
    assert "pentagon__vertex" in html
