"""
Zugriffsschutz-Matrix für alle Adressen der Social-App (Task 4.10,
Release-Durchsicht v1.2): Gate, Login-Pflicht, private und Bearbeiten-Adressen
leiten andere Personen auf das öffentliche Profil weiter, die Testhistorie ist
nirgends fremd sichtbar.

Die Matrix läuft über **alle** Adressmuster von `apps.social.urls` — eine
später hinzugefügte Adresse ohne Schutz fällt hier automatisch auf.
"""

import re

import pytest
from django.urls import reverse

from apps.accounts.models import ColorAssignment, Profile, User
from apps.colors.models import ColorCombination
from apps.quiz.models import TestResult
from apps.social import friendships, urls

pytestmark = pytest.mark.django_db

#: Adressen, die nur die eigene Person erreicht (owner_only, D-73).
OWNER_ONLY = [
    "profile_history",
    "profile_settings",
    "edit_nickname",
    "edit_bio",
    "edit_colors",
]

#: Adressen eines Profils, die jede angemeldete Person sehen darf.
PUBLIC_FOR_MEMBERS = ["profile_detail", "profile_friends"]

#: POST-Endpunkte für Freundschaften (Task 3.4).
ACTIONS = [
    "send_friend_request",
    "accept_friend_request",
    "decline_friend_request",
    "remove_friendship",
]

DUMMY = {"nickname": "someone", "pk": 1, "code": "w"}


def _patterns():
    """Alle Adressmuster der Social-App als (Name, Beispieladresse)."""
    result = []
    for pattern in urls.urlpatterns:
        parameters = set(pattern.pattern.regex.groupindex)
        kwargs = {key: value for key, value in DUMMY.items() if key in parameters}
        result.append((pattern.name, reverse(f"social:{pattern.name}", kwargs=kwargs)))
    return result


PATTERNS = _patterns()


def _profile(nickname):
    user = User.objects.create_user(
        email=f"{nickname}@example.com", password="a-long-enough-password"
    )
    return Profile.objects.create(user=user, nickname=nickname, bio=f"{nickname} bio")


@pytest.fixture
def alex():
    return _profile("alex")


@pytest.fixture
def jamie():
    return _profile("jamie")


def test_the_matrix_knows_every_url_of_the_social_app():
    known = set(OWNER_ONLY + PUBLIC_FOR_MEMBERS + ACTIONS) | {
        "search",
        "search_colors",
        "search_colors_combination",
    }

    assert {name for name, _path in PATTERNS} == known


# Gate: ohne Cookie ist alles gesperrt --------------------------------------------------


@pytest.mark.parametrize("name,path", PATTERNS)
def test_without_the_gate_cookie_every_address_is_locked(client, name, path):
    response = client.get(path)

    assert response.status_code == 302
    assert response.url.startswith("/gate/")


# Login-Pflicht: mit Gate-Cookie, aber ohne Anmeldung -----------------------------------


@pytest.mark.parametrize("name,path", PATTERNS)
def test_without_login_every_address_leads_to_the_login(gated_client, name, path):
    response = gated_client.get(path)

    assert response.status_code == 302
    assert "/accounts/login/" in response.url


@pytest.mark.parametrize("name,path", PATTERNS)
def test_without_login_post_leads_to_the_login_too(gated_client, name, path):
    response = gated_client.post(path)

    assert response.status_code == 302
    assert "/accounts/login/" in response.url


# Private und Bearbeiten-Adressen: andere werden weitergeleitet -------------------------


@pytest.mark.parametrize("name", OWNER_ONLY)
def test_another_person_is_redirected_to_the_public_profile(gated_client, alex, jamie, name):
    path = reverse(f"social:{name}", kwargs={"nickname": "jamie"})
    gated_client.force_login(alex.user)

    for method in (gated_client.get, gated_client.post):
        response = method(path)
        assert response.status_code == 302, (name, method)
        assert response.url == "/u/jamie/"
        assert response.content == b""


@pytest.mark.parametrize("name", OWNER_ONLY)
def test_the_own_person_reaches_the_address(gated_client, alex, name):
    gated_client.force_login(alex.user)

    response = gated_client.get(reverse(f"social:{name}", kwargs={"nickname": "alex"}))

    assert response.status_code == 200


@pytest.mark.parametrize("name", OWNER_ONLY + PUBLIC_FOR_MEMBERS)
def test_an_unknown_person_is_a_404(gated_client, alex, name):
    gated_client.force_login(alex.user)

    assert (
        gated_client.get(reverse(f"social:{name}", kwargs={"nickname": "nobody"})).status_code
        == 404
    )


# Die Testhistorie ist nirgends fremd sichtbar ------------------------------------------


def test_no_address_of_a_foreign_profile_ever_shows_the_history(gated_client, alex, jamie):
    """jamie hat drei Historieneinträge, einen davon übernommen (dessen Punkte
    sind gewollt sichtbar, D-70). Die beiden anderen dürfen auf **keiner**
    Adresse von jamies Profil auftauchen — weder Punkte noch Datum noch die
    Schaltflächen — und auch nicht auf der Suche oder in Listen."""
    adopted = TestResult.objects.create(
        profile=jamie,
        questionnaire_version=1,
        scores={"W": 9, "U": 10, "B": 6, "R": 2, "G": 3},
        result_colors="WU",
    )
    hidden = [
        TestResult.objects.create(
            profile=jamie,
            questionnaire_version=1,
            scores={"W": 17, "U": 18, "B": 19, "R": 20, "G": 21},
            result_colors="BR",
        ),
        TestResult.objects.create(
            profile=jamie,
            questionnaire_version=1,
            scores={"W": 31, "U": 32, "B": 33, "R": 34, "G": 35},
            result_colors="RG",
        ),
    ]
    ColorAssignment.objects.create(
        profile=jamie,
        author_profile=jamie,
        combination=ColorCombination.objects.get(code="WU", locale="en"),
        source=ColorAssignment.Source.SELF_TEST,
        test_result=adopted,
    )
    friendships.accept_request(friendships.send_request(alex, jamie), jamie)
    gated_client.force_login(alex.user)

    pages = ["/u/jamie/", "/u/jamie/friends/", "/search/?q=jamie", "/search/colors/w/"]
    pages += [f"/u/jamie/{tab}/" for tab in ("history", "settings", "edit/bio", "edit/colors")]
    for path in pages:
        html = gated_client.get(path, follow=True).content.decode()
        for result in hidden:
            assert f"/accounts/history/{result.pk}/" not in html, path
            assert f"/quiz/results/{result.pk}/adopt/" not in html, path
            assert ">17<" not in html and ">31<" not in html, path
        assert "Test history" not in _tabs(html), path


def _tabs(html):
    found = re.search(r'<nav class="profile-tabs".*?</nav>', html, re.S)
    return found.group(0) if found else ""


def test_history_entries_of_others_cannot_be_deleted_or_adopted(gated_client, alex, jamie):
    result = TestResult.objects.create(
        profile=jamie,
        questionnaire_version=1,
        scores={"W": 1, "U": 1, "B": 1, "R": 1, "G": 1},
        result_colors="W",
    )
    gated_client.force_login(alex.user)

    assert gated_client.post(f"/accounts/history/{result.pk}/delete/").status_code == 404
    assert gated_client.post(f"/quiz/results/{result.pk}/adopt/").status_code == 404
    assert TestResult.objects.filter(pk=result.pk).exists()
    assert not ColorAssignment.objects.filter(profile=alex).exists()
