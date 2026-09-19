"""
Tests für die gemeinsame Profilseite (Task 4.1, FR-P9, D-73): eigenes und
fremdes Profil sind dieselbe Seite unter `/u/<nickname>/`.
"""

import pytest

from apps.accounts.models import ColorAssignment, Profile, User
from apps.colors.models import ColorCombination
from apps.quiz.models import TestResult

pytestmark = pytest.mark.django_db


@pytest.fixture
def alex():
    user = User.objects.create_user(email="alex@example.com", password="a-long-enough-password")
    return Profile.objects.create(user=user, nickname="alex", bio="Alex bio.")


@pytest.fixture
def jamie():
    user = User.objects.create_user(email="jamie@example.com", password="a-long-enough-password")
    return Profile.objects.create(user=user, nickname="jamie", bio="Jamie bio.")


def _result(profile):
    return TestResult.objects.create(
        profile=profile,
        questionnaire_version=1,
        scores={"W": 9, "U": 10, "B": 6, "R": 2, "G": 3},
        result_colors="WU",
    )


# Eigene Person: Bearbeiten-Zugänge und Privates ---------------------------


def test_own_profile_shows_the_edit_form_and_private_sections(gated_client, alex):
    _result(alex)
    gated_client.force_login(alex.user)

    html = gated_client.get("/u/alex/").content.decode()

    assert 'href="/u/alex/edit/colors/"' in html
    assert 'href="/u/alex/edit/nickname/"' in html
    assert 'href="/u/alex/edit/bio/"' in html
    assert "Alex bio." in html
    assert 'href="/u/alex/history/"' in html
    assert 'href="/u/alex/settings/"' in html


def test_own_profile_offers_no_friend_action_against_oneself(gated_client, alex):
    gated_client.force_login(alex.user)

    html = gated_client.get("/u/alex/").content.decode()

    assert "Send friend request" not in html


def test_own_profile_is_found_case_insensitively(gated_client, alex):
    gated_client.force_login(alex.user)

    response = gated_client.get("/u/ALEX/")

    assert response.status_code == 200
    assert 'href="/u/alex/edit/colors/"' in response.content.decode()


# Fremde Person: nichts davon ------------------------------------------------


def test_foreign_profile_shows_no_edit_form_and_no_private_sections(gated_client, alex, jamie):
    _result(jamie)
    gated_client.force_login(alex.user)

    html = gated_client.get("/u/jamie/").content.decode()

    assert "/edit/" not in html
    assert "/history/" not in html
    assert "/settings/" not in html
    assert "Jamie bio." in html
    assert "Send friend request" in html


# Alte Adresse ---------------------------------------------------------------


def test_the_old_profile_address_redirects_to_the_new_one(gated_client, alex):
    gated_client.force_login(alex.user)

    response = gated_client.get("/accounts/profile/")

    assert response.status_code == 302
    assert response.url == "/u/alex/"


def test_an_account_without_a_profile_gets_a_404_on_the_old_address(gated_client):
    user = User.objects.create_superuser(email="root@example.com", password="a-long-enough-pw")
    gated_client.force_login(user)

    assert gated_client.get("/accounts/profile/").status_code == 404


def test_the_old_address_no_longer_saves_anything(gated_client, alex):
    gated_client.force_login(alex.user)

    response = gated_client.post("/accounts/profile/", {"colors": ["W"]})

    assert response.status_code == 405
    assert not ColorAssignment.objects.filter(profile=alex).exists()


def test_deleting_a_history_entry_returns_to_the_history_tab(gated_client, alex):
    result = _result(alex)
    gated_client.force_login(alex.user)

    response = gated_client.post(f"/accounts/history/{result.pk}/delete/")

    assert response.url == "/u/alex/history/"


def test_adopting_a_result_returns_to_the_profile_page(gated_client, alex):
    result = _result(alex)
    gated_client.force_login(alex.user)

    response = gated_client.post(f"/quiz/results/{result.pk}/adopt/")

    assert response.url == "/u/alex/"
    assert ColorAssignment.objects.get(profile=alex).combination == ColorCombination.objects.get(
        code="WU", locale="en"
    )


def test_the_header_link_points_to_the_profile_page(gated_client, alex):
    gated_client.force_login(alex.user)

    html = gated_client.get("/colors/").content.decode()

    assert 'href="/u/alex/">alex</a>' in html


# Nickname taugt als Adressbestandteil ------------------------------------------


def test_registration_rejects_a_nickname_with_a_slash(gated_client):
    response = gated_client.post(
        "/accounts/register/",
        {
            "email": "new@example.com",
            "nickname": "a/b",
            "password1": "a-long-enough-password",
            "password2": "a-long-enough-password",
        },
    )

    assert response.status_code == 200
    assert not Profile.objects.filter(nickname="a/b").exists()
