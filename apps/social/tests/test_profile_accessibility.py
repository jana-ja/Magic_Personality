"""
Tests für Mobil-Layout und Barrierefreiheit des Profils (Task 4.9, FR-P16,
NFR-3, NFR-5, NFR-6, D-73). Was nur ein echter Browser prüfen kann (Fokus,
Trefferflächen, Scrollen bei 375 px), ist in docs/ROADMAP.md dokumentiert; hier
steht, was sich am ausgelieferten HTML und den Dateien festhalten lässt.
"""

import re

import pytest
from django.conf import settings

from apps.accounts.models import ColorAssignment, Profile, User
from apps.colors.models import ColorCombination
from apps.quiz.models import TestResult
from apps.social import friendships

pytestmark = pytest.mark.django_db


def _profile(nickname):
    user = User.objects.create_user(
        email=f"{nickname}@example.com", password="a-long-enough-password"
    )
    return Profile.objects.create(user=user, nickname=nickname, bio="Bio.")


@pytest.fixture
def alex():
    profile = _profile("alex")
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
    friendships.send_request(_profile("jamie"), profile)
    return profile


def _static(name):
    return (settings.BASE_DIR / "static" / name).read_text(encoding="utf-8")


def _page(client, user, path):
    client.force_login(user)
    return client.get(path).content.decode()


PAGES = [
    "/u/alex/",
    "/u/alex/friends/",
    "/u/alex/history/",
    "/u/alex/settings/",
    "/u/alex/edit/bio/",
    "/u/alex/edit/nickname/",
    "/u/alex/edit/colors/",
]


# Landmarks und Navigation ---------------------------------------------------------------------


@pytest.mark.parametrize("path", PAGES)
def test_every_profile_page_has_one_h1_and_a_labelled_tab_navigation(gated_client, alex, path):
    html = _page(gated_client, alex.user, path)

    assert html.count("<h1") == 1
    nav = re.search(r'<nav class="profile-tabs" aria-label="[^"]+"', html)
    assert nav is not None
    assert 'role="tablist"' not in html
    assert 'role="tab"' not in html


@pytest.mark.parametrize("path", PAGES)
def test_every_section_and_card_is_labelled_by_its_heading(gated_client, alex, path):
    html = _page(gated_client, alex.user, path)

    for label_id in re.findall(r'aria-labelledby="([^"]+)"', html):
        assert f'id="{label_id}"' in html, label_id


@pytest.mark.parametrize("path", PAGES)
def test_a_profile_page_has_no_duplicate_ids(gated_client, alex, path):
    html = _page(gated_client, alex.user, path)
    ids = re.findall(r'\sid="([^"]+)"', html)

    assert len(ids) == len(set(ids))


def test_the_sidebar_is_a_labelled_landmark(gated_client, alex):
    html = _page(gated_client, alex.user, "/u/alex/")

    assert re.search(r'<aside class="profile-layout__side" aria-label="[^"]+"', html)


def test_the_history_and_the_requests_are_labelled_sections(gated_client, alex):
    history = _page(gated_client, alex.user, "/u/alex/history/")
    friends = _page(gated_client, alex.user, "/u/alex/friends/")

    assert 'aria-labelledby="history-heading"' in history
    assert 'aria-labelledby="requests-heading"' in friends


# Screenreader: Balken, Verlauf, Schaltflächen -----------------------------------------------------


def test_the_score_bars_name_each_color_for_screen_readers(gated_client, alex):
    html = _page(gated_client, alex.user, "/u/alex/")
    bars = re.search(r'<ul class="score-bars"[^>]*>.*?</ul>', html, re.S).group(0)

    assert "aria-label=" in bars.split(">")[0]
    assert bars.count('class="visually-hidden"') == 5


def test_the_history_buttons_say_which_result_they_act_on(gated_client, alex):
    html = _page(gated_client, alex.user, "/u/alex/history/")

    assert re.search(r'aria-label="Delete the .* result from \d{4}-\d{2}-\d{2}"', html)


def test_the_history_cells_carry_labels_for_the_stacked_mobile_layout(gated_client, alex):
    html = _page(gated_client, alex.user, "/u/alex/history/")

    assert 'data-label="Date"' in html
    assert 'data-label="Result"' in html
    assert 'data-label="Points"' in html


# Live-Region und Skript ------------------------------------------------------------


def test_the_live_region_lives_outside_the_swapped_sections(gated_client, alex):
    html = _page(gated_client, alex.user, "/u/alex/")
    live = html.index('id="profile-live-region"')

    for section in ("profile-name", "profile-bio", "profile-colors"):
        assert live < html.index(f'id="{section}"')
    assert 'aria-live="polite"' in html
    for text in ("data-editing-text", "data-saved-text", "data-cancelled-text"):
        assert text in html


def test_the_live_region_is_not_part_of_any_swapped_section(gated_client, alex):
    html = _page(gated_client, alex.user, "/u/alex/edit/bio/")
    section = re.search(r'<section id="profile-bio".*?</section>', html, re.S).group(0)

    assert "profile-live-region" not in section


def test_the_sections_script_is_loaded_and_tied_to_the_live_region(gated_client, alex):
    html = _page(gated_client, alex.user, "/u/alex/")
    script = _static("js/profile_sections.js")

    assert "js/profile_sections.js" in html
    assert "profile-live-region" in script
    assert all(section in script for section in ("profile-bio", "profile-colors", "profile-name"))
    assert "focus()" in script


@pytest.mark.parametrize("name", ["profile_sections.js", "profile_colors.js"])
def test_the_own_scripts_stay_small_and_free_of_frameworks(name):
    script = _static(f"js/{name}")

    assert len(script.splitlines()) < 60
    assert "import " not in script
    assert "require(" not in script


def test_the_total_of_own_javascript_stays_reasonable():
    """ARCHITECTURE.md §4.3: eigenes JavaScript ohne Framework, klein gehalten."""
    lines = sum(
        len(_static(f"js/{name}").splitlines())
        for name in (
            "main.js",
            "profile_colors.js",
            "profile_sections.js",
            "quiz.js",
            "quiz_claim.js",
        )
    )

    assert lines < 320


# Trefferflächen und Layout (Stylesheet) ------------------------------------------


def test_touch_targets_are_at_least_44px_high():
    """Die gemeinsame Regel für Tabs, Bearbeiten-Links, Autorenkarten und
    Schaltflächen des Profils (2.75rem = 44px bei 16px Schrift)."""
    css = _static("css/base.css")
    rule = re.search(r"(\.profile-tabs a,[^{]*)\{([^}]*)\}", css)

    assert rule is not None
    selectors, body = rule.groups()
    for selector in (".profile-edit-link", ".author-card__name", ".test-history button"):
        assert selector in selectors
    assert "min-height: 2.75rem" in body


def test_the_history_table_stacks_on_small_screens():
    css = _static("css/base.css")

    assert "content: attr(data-label)" in css


def test_the_sidebar_lands_below_the_main_area_on_small_screens():
    css = _static("css/base.css")
    layout = re.search(r"\.profile-layout \{[^}]*\}", css).group(0)

    assert "grid-template-columns: minmax(0, 1fr);" in layout
