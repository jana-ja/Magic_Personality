"""
Tests für die privaten Tabs Testhistorie und Einstellungen (Task 4.4,
FR-P6, FR-P7, D-19, D-73): nur die eigene Person erreicht sie, jede andere
wird auf das öffentliche Profil der Adresse weitergeleitet.
"""

import re

import pytest

from apps.accounts.models import ColorAssignment, Profile, User
from apps.colors.models import ColorCombination
from apps.quiz.models import TestResult

pytestmark = pytest.mark.django_db

PRIVATE = ["history", "settings"]


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


def _result(profile, scores=None, colors="WU"):
    return TestResult.objects.create(
        profile=profile,
        questionnaire_version=1,
        scores=scores or {"W": 9, "U": 10, "B": 6, "R": 2, "G": 3},
        result_colors=colors,
    )


def _tabs(html):
    return re.search(r'<nav class="profile-tabs".*?</nav>', html, re.S).group(0)


# Eigene Person -----------------------------------------------------------------


def test_own_history_tab_lists_entries_with_adopt_and_delete(gated_client, alex):
    result = _result(alex)
    gated_client.force_login(alex.user)

    html = gated_client.get("/u/alex/history/").content.decode()

    assert "W: 9, U: 10, B: 6, R: 2, G: 3" in html
    assert f'action="/quiz/results/{result.pk}/adopt/"' in html
    assert f'action="/accounts/history/{result.pk}/delete/"' in html


def test_own_settings_tab_links_password_change_and_account_deletion(gated_client, alex):
    gated_client.force_login(alex.user)

    html = gated_client.get("/u/alex/settings/").content.decode()

    assert 'href="/accounts/password/change/"' in html
    assert 'href="/accounts/delete/"' in html


def test_the_private_tabs_appear_for_the_own_person_only(gated_client, alex, jamie):
    gated_client.force_login(alex.user)

    own = _tabs(gated_client.get("/u/alex/").content.decode())
    foreign = _tabs(gated_client.get("/u/jamie/").content.decode())

    assert 'href="/u/alex/history/"' in own
    assert 'href="/u/alex/settings/"' in own
    assert "/history/" not in foreign
    assert "/settings/" not in foreign


@pytest.mark.parametrize("tab", PRIVATE)
def test_the_private_tab_is_marked_current(gated_client, alex, tab):
    gated_client.force_login(alex.user)

    tabs = _tabs(gated_client.get(f"/u/alex/{tab}/").content.decode())

    assert re.findall(r'<a href="([^"]+)" aria-current="page"', tabs) == [f"/u/alex/{tab}/"]


def test_history_and_account_deletion_are_gone_from_the_pinboard_tab(gated_client, alex):
    _result(alex)
    gated_client.force_login(alex.user)

    html = gated_client.get("/u/alex/").content.decode()

    assert "test-history" not in html
    assert 'href="/accounts/delete/"' not in html


# Andere Person: Weiterleitung auf das öffentliche Profil ------------------------------


@pytest.mark.parametrize("tab", PRIVATE)
def test_another_person_is_redirected_to_the_public_profile(gated_client, alex, jamie, tab):
    gated_client.force_login(alex.user)

    response = gated_client.get(f"/u/jamie/{tab}/")

    assert response.status_code == 302
    assert response.url == "/u/jamie/"


@pytest.mark.parametrize("tab", PRIVATE)
def test_the_redirect_carries_nothing_private(gated_client, alex, jamie, tab):
    _result(jamie, scores={"W": 1, "U": 2, "B": 3, "R": 4, "G": 5})
    gated_client.force_login(alex.user)

    response = gated_client.get(f"/u/jamie/{tab}/")

    assert response.content == b""
    assert "W: 1" not in gated_client.get(response.url).content.decode()


@pytest.mark.parametrize("tab", PRIVATE)
def test_following_the_redirect_never_shows_foreign_history(gated_client, alex, jamie, tab):
    result = _result(jamie)
    gated_client.force_login(alex.user)

    html = gated_client.get(f"/u/jamie/{tab}/", follow=True).content.decode()

    assert f"/accounts/history/{result.pk}/delete/" not in html
    assert f"/quiz/results/{result.pk}/adopt/" not in html
    assert "Delete account" not in html


@pytest.mark.parametrize("tab", PRIVATE)
def test_the_redirect_also_applies_to_post(gated_client, alex, jamie, tab):
    gated_client.force_login(alex.user)

    response = gated_client.post(f"/u/jamie/{tab}/")

    assert response.status_code == 302
    assert response.url == "/u/jamie/"


def test_the_nickname_in_the_address_is_matched_case_insensitively(gated_client, alex, jamie):
    gated_client.force_login(alex.user)

    assert gated_client.get("/u/ALEX/history/").status_code == 200
    assert gated_client.get("/u/JAMIE/history/").url == "/u/jamie/"


# Gäste und Unbekannte ---------------------------------------------------------------


@pytest.mark.parametrize("tab", PRIVATE)
def test_guests_are_sent_to_the_login(gated_client, jamie, tab):
    response = gated_client.get(f"/u/jamie/{tab}/")

    assert response.status_code == 302
    assert "/accounts/login/" in response.url


@pytest.mark.parametrize("tab", PRIVATE)
def test_an_unknown_person_is_a_404(gated_client, alex, tab):
    gated_client.force_login(alex.user)

    assert gated_client.get(f"/u/nobody/{tab}/").status_code == 404


# Aktionen der Historie ----------------------------------------------------------------


def test_deleting_from_the_history_stays_on_the_history_tab(gated_client, alex):
    result = _result(alex)
    gated_client.force_login(alex.user)

    response = gated_client.post(f"/accounts/history/{result.pk}/delete/")

    assert response.url == "/u/alex/history/"
    assert not TestResult.objects.filter(pk=result.pk).exists()


def test_adopting_a_result_from_the_history_shows_it_in_the_profile(gated_client, alex):
    result = _result(alex)
    gated_client.force_login(alex.user)

    response = gated_client.post(f"/quiz/results/{result.pk}/adopt/")

    assert response.url == "/u/alex/"
    assignment = ColorAssignment.objects.get(profile=alex)
    assert assignment.test_result == result
    assert assignment.combination == ColorCombination.objects.get(code="WU", locale="en")
