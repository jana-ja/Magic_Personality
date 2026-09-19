"""
Tests für das einzelne Bearbeiten von Nickname und Bio (Task 4.5, FR-P12,
FR-P2, D-72, D-73): jeder Bereich hat ein eigenes Formular und speichert
ausschließlich sich selbst.
"""

import re

import pytest

from apps.accounts.models import ColorAssignment, Profile, User
from apps.colors.models import ColorCombination
from apps.quiz.models import TestResult

pytestmark = pytest.mark.django_db


def _profile(nickname, bio=""):
    user = User.objects.create_user(
        email=f"{nickname}@example.com", password="a-long-enough-password"
    )
    return Profile.objects.create(user=user, nickname=nickname, bio=bio)


@pytest.fixture
def alex():
    return _profile("alex", bio="Alex bio.")


@pytest.fixture
def jamie():
    return _profile("jamie", bio="Jamie bio.")


def _adopted(profile):
    result = TestResult.objects.create(
        profile=profile,
        questionnaire_version=1,
        scores={"W": 9, "U": 10, "B": 6, "R": 2, "G": 3},
        result_colors="WU",
    )
    ColorAssignment.objects.create(
        profile=profile,
        author_profile=profile,
        combination=ColorCombination.objects.get(code="WU", locale="en"),
        source=ColorAssignment.Source.SELF_TEST,
        test_result=result,
    )
    return result


def _section(html, element_id):
    return re.search(rf'id="{element_id}".*?</(?:div|section)>', html, re.S).group(0)


# Ansicht: nur ein Bereich im Bearbeiten-Modus ------------------------------------------


def test_the_edit_links_are_offered_to_the_own_person_only(gated_client, alex, jamie):
    gated_client.force_login(alex.user)

    own = gated_client.get("/u/alex/").content.decode()
    foreign = gated_client.get("/u/jamie/").content.decode()

    assert 'href="/u/alex/edit/nickname/"' in own
    assert 'href="/u/alex/edit/bio/"' in own
    assert "/edit/" not in foreign


def test_the_nickname_edit_page_shows_only_the_nickname_form(gated_client, alex):
    gated_client.force_login(alex.user)

    html = gated_client.get("/u/alex/edit/nickname/").content.decode()

    assert 'action="/u/alex/edit/nickname/"' in html
    assert 'name="nickname"' in html
    assert 'action="/u/alex/edit/bio/"' not in html
    assert 'name="bio"' not in html


def test_the_bio_edit_page_shows_only_the_bio_form(gated_client, alex):
    gated_client.force_login(alex.user)

    html = gated_client.get("/u/alex/edit/bio/").content.decode()

    assert 'action="/u/alex/edit/bio/"' in html
    assert 'name="bio"' in html
    assert "Alex bio." in html
    assert 'name="nickname"' not in html


def test_the_edit_links_carry_the_htmx_attributes_for_an_in_place_swap(gated_client, alex):
    gated_client.force_login(alex.user)

    html = gated_client.get("/u/alex/").content.decode()

    assert 'hx-get="/u/alex/edit/nickname/"' in html
    assert 'hx-select="#profile-name"' in html
    assert 'hx-get="/u/alex/edit/bio/"' in html
    assert 'hx-select="#profile-bio"' in html


def test_the_edit_forms_have_the_sections_the_swap_selects(gated_client, alex):
    """hx-select holt `#profile-name` bzw. `#profile-bio` aus der Bearbeiten-Seite:
    beide müssen dort genau einmal vorkommen (keine doppelten ids)."""
    gated_client.force_login(alex.user)

    nick = gated_client.get("/u/alex/edit/nickname/").content.decode()
    bio = gated_client.get("/u/alex/edit/bio/").content.decode()

    assert nick.count('id="profile-name"') == 1
    assert 'name="nickname"' in _section(nick, "profile-name")
    assert bio.count('id="profile-bio"') == 1
    assert 'name="bio"' in _section(bio, "profile-bio")


def test_cancel_returns_to_the_profile_without_saving(gated_client, alex):
    gated_client.force_login(alex.user)

    html = gated_client.get("/u/alex/edit/bio/").content.decode()

    assert 'href="/u/alex/"' in _section(html, "profile-bio")
    alex.refresh_from_db()
    assert alex.bio == "Alex bio."


# Speichern: jeder Bereich nur sich selbst --------------------------------------------------


def test_saving_the_bio_changes_only_the_bio(gated_client, alex):
    result = _adopted(alex)
    gated_client.force_login(alex.user)

    response = gated_client.post("/u/alex/edit/bio/", {"bio": "New bio."})

    assert response.status_code == 302
    assert response.url == "/u/alex/"
    alex.refresh_from_db()
    assert alex.bio == "New bio."
    assert alex.nickname == "alex"
    assignment = ColorAssignment.objects.get(profile=alex)
    assert assignment.source == ColorAssignment.Source.SELF_TEST
    assert assignment.test_result == result


def test_saving_the_nickname_changes_only_the_nickname(gated_client, alex):
    result = _adopted(alex)
    gated_client.force_login(alex.user)

    response = gated_client.post("/u/alex/edit/nickname/", {"nickname": "alexandra"})

    assert response.status_code == 302
    alex.refresh_from_db()
    assert alex.nickname == "alexandra"
    assert alex.bio == "Alex bio."
    assert ColorAssignment.objects.get(profile=alex).test_result == result


def test_the_nickname_form_ignores_a_bio_sent_along(gated_client, alex):
    gated_client.force_login(alex.user)

    gated_client.post("/u/alex/edit/nickname/", {"nickname": "alex2", "bio": "Sneaky."})

    alex.refresh_from_db()
    assert alex.bio == "Alex bio."


def test_the_bio_form_ignores_a_nickname_sent_along(gated_client, alex):
    gated_client.force_login(alex.user)

    gated_client.post("/u/alex/edit/bio/", {"bio": "Fine.", "nickname": "hijacked"})

    alex.refresh_from_db()
    assert alex.nickname == "alex"


def test_an_empty_bio_clears_the_bio(gated_client, alex):
    gated_client.force_login(alex.user)

    gated_client.post("/u/alex/edit/bio/", {"bio": ""})

    alex.refresh_from_db()
    assert alex.bio == ""


def test_a_new_nickname_leads_to_the_new_address(gated_client, alex):
    gated_client.force_login(alex.user)

    response = gated_client.post("/u/alex/edit/nickname/", {"nickname": "alexandra"})

    assert response.url == "/u/alexandra/"
    assert gated_client.get(response.url).status_code == 200
    assert gated_client.get("/accounts/profile/").url == "/u/alexandra/"
    assert "alexandra" in gated_client.get("/colors/").content.decode()


# Validierung -------------------------------------------------------------------------------


def test_a_taken_nickname_is_reported_and_nothing_changes(gated_client, alex, jamie):
    gated_client.force_login(alex.user)

    response = gated_client.post("/u/alex/edit/nickname/", {"nickname": "JAMIE"})

    assert response.status_code == 200
    assert "already taken" in response.content.decode()
    alex.refresh_from_db()
    assert alex.nickname == "alex"


def test_keeping_the_own_nickname_is_not_a_collision(gated_client, alex):
    gated_client.force_login(alex.user)

    response = gated_client.post("/u/alex/edit/nickname/", {"nickname": "Alex"})

    assert response.status_code == 302
    alex.refresh_from_db()
    assert alex.nickname == "Alex"


@pytest.mark.parametrize("nickname", ["a/b", "..", ".", ""])
def test_nicknames_that_do_not_work_as_an_address_are_rejected(gated_client, alex, nickname):
    gated_client.force_login(alex.user)

    response = gated_client.post("/u/alex/edit/nickname/", {"nickname": nickname})

    assert response.status_code == 200
    assert 'class="form-errors"' in response.content.decode()
    alex.refresh_from_db()
    assert alex.nickname == "alex"


def test_a_too_long_nickname_is_rejected(gated_client, alex):
    gated_client.force_login(alex.user)

    response = gated_client.post("/u/alex/edit/nickname/", {"nickname": "x" * 51})

    assert response.status_code == 200
    alex.refresh_from_db()
    assert alex.nickname == "alex"


# Nur die eigene Person -------------------------------------------------------------------


@pytest.mark.parametrize("section", ["nickname", "bio"])
def test_another_person_is_redirected_on_get(gated_client, alex, jamie, section):
    gated_client.force_login(alex.user)

    response = gated_client.get(f"/u/jamie/edit/{section}/")

    assert response.status_code == 302
    assert response.url == "/u/jamie/"
    assert response.content == b""


@pytest.mark.parametrize(
    "section,data",
    [("nickname", {"nickname": "hijacked"}), ("bio", {"bio": "Hijacked."})],
)
def test_another_person_is_redirected_on_post_and_nothing_changes(
    gated_client, alex, jamie, section, data
):
    gated_client.force_login(alex.user)

    response = gated_client.post(f"/u/jamie/edit/{section}/", data)

    assert response.status_code == 302
    assert response.url == "/u/jamie/"
    jamie.refresh_from_db()
    assert jamie.nickname == "jamie"
    assert jamie.bio == "Jamie bio."


@pytest.mark.parametrize("section", ["nickname", "bio"])
def test_guests_are_sent_to_the_login(gated_client, jamie, section):
    response = gated_client.post(f"/u/jamie/edit/{section}/", {"nickname": "x", "bio": "x"})

    assert response.status_code == 302
    assert "/accounts/login/" in response.url
    jamie.refresh_from_db()
    assert jamie.nickname == "jamie"


@pytest.mark.parametrize("section", ["nickname", "bio"])
def test_an_unknown_person_is_a_404(gated_client, alex, section):
    gated_client.force_login(alex.user)

    assert gated_client.get(f"/u/nobody/edit/{section}/").status_code == 404


# Farben bleiben unberührt --------------------------------------------------------------------


def test_the_colors_form_no_longer_carries_nickname_or_bio(gated_client, alex):
    gated_client.force_login(alex.user)

    html = gated_client.get("/u/alex/").content.decode()
    form = re.search(r'<form method="post" action="/accounts/profile/">.*?</form>', html, re.S)

    assert 'name="colors"' in form.group(0)
    assert 'name="nickname"' not in form.group(0)
    assert 'name="bio"' not in form.group(0)


def test_saving_the_colors_leaves_nickname_and_bio_alone(gated_client, alex):
    gated_client.force_login(alex.user)

    gated_client.post("/accounts/profile/", {"colors": ["W", "U"], "nickname": "x", "bio": "x"})

    alex.refresh_from_db()
    assert alex.nickname == "alex"
    assert alex.bio == "Alex bio."
    assert ColorAssignment.objects.get(profile=alex).combination.code == "WU"


def test_the_bio_form_also_refreshes_the_short_bio_in_the_header(gated_client, alex):
    """Nach dem Austausch nur des About-Bereichs bliebe die Kurzfassung im Kopf
    veraltet — `hx-select-oob` zieht `#profile-head-bio` mit."""
    gated_client.force_login(alex.user)

    edit = gated_client.get("/u/alex/edit/bio/").content.decode()
    profile = gated_client.get("/u/alex/").content.decode()

    assert 'hx-select-oob="#profile-head-bio"' in edit
    assert profile.count('id="profile-head-bio"') == 1
    assert "Alex bio." in _section(profile, "profile-head-bio")
