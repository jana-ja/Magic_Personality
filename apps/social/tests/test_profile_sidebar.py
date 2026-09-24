"""
Tests für die Pinnwand-Sidebar (Task 4.7, FR-P14, D-70, D-73): alle
Kartenzustände rendern fehlerfrei. Die Pinnwand selbst (Task 7.2, FR-B22)
kommt mit echten Pins in `test_pinboard_tab.py`; hier nur ihr Leerzustand,
weil `alex`/`jamie` in diesem Modul nie etwas pinnen.
"""

import re

import pytest

from apps.accounts.models import ColorAssignment, Profile, User
from apps.colors.models import ColorCombination
from apps.quiz.models import TestResult
from apps.social import friendships

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


def _assign(profile, code="WU", scores=None):
    result = None
    if scores:
        result = TestResult.objects.create(
            profile=profile, questionnaire_version=1, scores=scores, result_colors=code
        )
    return ColorAssignment.objects.create(
        profile=profile,
        author_profile=profile,
        combination=ColorCombination.objects.get(code=code, locale="en"),
        source=ColorAssignment.Source.SELF_TEST if result else ColorAssignment.Source.SELF_MANUAL,
        test_result=result,
    )


def _befriend(a, b):
    friendships.accept_request(friendships.send_request(a, b), b)


def _get(client, viewer, path="/u/jamie/"):
    client.force_login(viewer.user)
    return client.get(path).content.decode()


def _card(html, element_id):
    return re.search(rf'<section id="{element_id}".*?</section>', html, re.S).group(0)


def _friends_card(html):
    return re.search(
        r'<section class="profile-card" aria-labelledby="friends-card-heading">.*?</section>',
        html,
        re.S,
    ).group(0)


# Pinnwand ------------------------------------------------------------------------------------


def test_the_empty_pinboard_shows_the_owners_hint_on_the_own_profile(gated_client, alex):
    html = _get(gated_client, alex, "/u/alex/")

    assert "haven't pinned anything yet" in html
    assert "Pin" in html


def test_the_empty_pinboard_shows_a_plain_note_on_a_foreign_profile(gated_client, alex, jamie):
    html = _get(gated_client, alex, "/u/jamie/")

    assert "Nothing pinned yet." in html


def test_the_empty_pinboard_offers_no_dead_buttons_or_links(gated_client, alex, jamie):
    html = _get(gated_client, alex)
    section = re.search(r'<section class="profile-pinboard".*?</section>', html, re.S).group(0)

    assert "<a " not in section
    assert "<button" not in section
    assert "<form" not in section


def test_the_sidebar_comes_after_the_main_area_so_it_lands_below_on_mobile(
    gated_client, alex, jamie
):
    html = _get(gated_client, alex)

    assert html.index("profile-layout__main") < html.index("profile-layout__side")
    assert html.index("profile-pinboard") < html.index('id="profile-bio"')


def test_the_sidebar_is_only_on_the_pinboard_tab(gated_client, alex, jamie):
    html = _get(gated_client, alex, "/u/jamie/friends/")

    assert "profile-layout__side" not in html


# Bio-Karte -------------------------------------------------------------------------------------


def test_the_bio_card_shows_the_bio(gated_client, alex, jamie):
    card = _card(_get(gated_client, alex), "profile-bio")

    assert "Jamie bio." in card


def test_the_bio_card_without_a_bio_shows_a_hint(gated_client, alex, jamie):
    jamie.bio = ""
    jamie.save()

    card = _card(_get(gated_client, alex), "profile-bio")

    assert "No bio yet." in card
    assert "/edit/" not in card


def test_the_own_bio_card_offers_edit_or_add(gated_client, alex):
    with_bio = _card(_get(gated_client, alex, "/u/alex/"), "profile-bio")
    alex.bio = ""
    alex.save()
    without = _card(_get(gated_client, alex, "/u/alex/"), "profile-bio")

    assert 'href="/u/alex/edit/bio/"' in with_bio and "Edit bio" in with_bio
    assert 'href="/u/alex/edit/bio/"' in without and "Add a bio" in without


# Farben-Karte ------------------------------------------------------------------------------------


def test_the_colors_card_without_colors_shows_a_hint(gated_client, alex, jamie):
    card = _card(_get(gated_client, alex), "profile-colors")

    assert "No colors set yet." in card
    assert "score-bar" not in card


def test_the_colors_card_links_the_combination_without_a_test_link(gated_client, alex, jamie):
    _assign(jamie, "UB")

    card = _card(_get(gated_client, alex), "profile-colors")

    assert 'href="/colors/ub/"' in card
    assert "score-bar" not in card
    assert "From your test result" not in card


def test_the_colors_card_shows_bars_with_letter_and_number_for_an_adopted_result(
    gated_client, alex, jamie
):
    _assign(jamie, "WU", {"W": 9, "U": 10, "B": 6, "R": 2, "G": 3})

    card = _card(_get(gated_client, alex), "profile-colors")

    labels = re.findall(r'score-bar__label">(\w)</span>', card)
    values = re.findall(r'score-bar__value">(\d+)</span>', card)
    assert labels == ["W", "U", "B", "R", "G"]
    assert values == ["9", "10", "6", "2", "3"]


def test_the_bars_are_scaled_to_the_highest_score(gated_client, alex, jamie):
    _assign(jamie, "WU", {"W": 5, "U": 10, "B": 0, "R": 0, "G": 0})

    card = _card(_get(gated_client, alex), "profile-colors")

    assert re.findall(r"--bar-width: (\d+)%", card) == ["50", "100", "0", "0", "0"]


def test_all_zero_scores_do_not_break_the_bars(gated_client, alex, jamie):
    _assign(jamie, "WU", {"W": 0, "U": 0, "B": 0, "R": 0, "G": 0})

    card = _card(_get(gated_client, alex), "profile-colors")

    assert re.findall(r"--bar-width: (\d+)%", card) == ["0"] * 5


def test_the_own_card_says_when_the_colors_come_from_the_test(gated_client, alex):
    _assign(alex, "WU", {"W": 9, "U": 10, "B": 6, "R": 2, "G": 3})

    card = _card(_get(gated_client, alex, "/u/alex/"), "profile-colors")

    assert "From your test result." in card
    assert 'href="/u/alex/edit/colors/"' in card


def test_the_own_card_for_manual_colors_has_no_test_hint_but_an_edit_link(gated_client, alex):
    _assign(alex, "UB")

    card = _card(_get(gated_client, alex, "/u/alex/"), "profile-colors")

    assert "From your test result" not in card
    assert 'href="/u/alex/edit/colors/"' in card


def test_only_the_adopted_result_is_ever_shown_not_the_history(gated_client, alex, jamie):
    _assign(jamie, "WU", {"W": 9, "U": 10, "B": 6, "R": 2, "G": 3})
    TestResult.objects.create(
        profile=jamie,
        questionnaire_version=1,
        scores={"W": 1, "U": 2, "B": 3, "R": 4, "G": 5},
        result_colors="RG",
    )

    html = _get(gated_client, alex)

    assert re.findall(r'score-bar__value">(\d+)</span>', html) == ["9", "10", "6", "2", "3"]


# Freunde-Karte ------------------------------------------------------------------


def test_the_friends_card_without_friends_shows_a_hint(gated_client, alex, jamie):
    card = _friends_card(_get(gated_client, alex))

    assert "No friends yet." in card
    assert "Show all friends" not in card


def test_the_friends_card_lists_friends_and_links_to_the_tab(gated_client, alex, jamie):
    for name in ("taylor", "robin"):
        _befriend(jamie, _profile(name))

    card = _friends_card(_get(gated_client, alex))

    assert 'href="/u/taylor/"' in card
    assert 'href="/u/robin/"' in card
    assert 'href="/u/jamie/friends/"' in card
    assert ">2<" in card


def test_the_friends_card_shows_at_most_eight_friends(gated_client, alex, jamie):
    for index in range(11):
        _befriend(jamie, _profile(f"friend{index:02d}"))

    card = _friends_card(_get(gated_client, alex))

    assert len(re.findall(r'class="author-card__name" href="/u/friend', card)) == 8
    assert ">11<" in card
    full = _get(gated_client, alex, "/u/jamie/friends/")
    assert len(re.findall(r'class="author-card__name" href="/u/friend', full)) == 11


def test_the_friends_in_the_card_stay_clickable_on_the_own_profile(gated_client, alex, jamie):
    _befriend(alex, jamie)

    card = _friends_card(_get(gated_client, alex, "/u/alex/"))

    assert 'href="/u/jamie/"' in card


# Fremde Sicht: nichts Privates in der Sidebar ---------------------------------


def test_the_foreign_sidebar_has_no_edit_links(gated_client, alex, jamie):
    _assign(jamie, "WU", {"W": 9, "U": 10, "B": 6, "R": 2, "G": 3})

    html = _get(gated_client, alex)
    side = html[html.index("profile-layout__side") :]

    assert "/edit/" not in side
    assert "Edit " not in side
