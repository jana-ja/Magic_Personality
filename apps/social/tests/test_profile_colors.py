"""
Tests für das Bearbeiten der Farben (Task 4.6, FR-P4, FR-P5, FR-P13, D-72,
D-74): ein Testergebnis der Historie übernehmen oder 1 bis 5 Farben manuell
wählen, mit dem Fünfeck als Bedienhilfe über den Kontrollkästchen.
"""

import re

import pytest

from apps.accounts.models import ColorAssignment, Profile, User
from apps.colors.models import Color, ColorCombination
from apps.quiz.models import TestResult

pytestmark = pytest.mark.django_db


def _bars(html):
    """Punkte je Farbe aus den Balken der Sidebar (Buchstabe und Zahl, Task 4.7)."""
    return dict(
        (code, int(points))
        for code, points in re.findall(
            r'score-bar__label">(\w)</span>.*?score-bar__value">(\d+)</span>', html, re.S
        )
    )


URL = "/u/alex/edit/colors/"


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


def _result(profile, colors="WU", scores=None):
    return TestResult.objects.create(
        profile=profile,
        questionnaire_version=1,
        scores=scores or {"W": 9, "U": 10, "B": 6, "R": 2, "G": 3},
        result_colors=colors,
    )


def _assign(profile, code, result=None):
    return ColorAssignment.objects.create(
        profile=profile,
        author_profile=profile,
        combination=ColorCombination.objects.get(code=code, locale="en"),
        source=ColorAssignment.Source.SELF_TEST if result else ColorAssignment.Source.SELF_MANUAL,
        test_result=result,
    )


def _form(html):
    return re.search(
        r'<form method="post" action="/u/alex/edit/colors/".*?</form>', html, re.S
    ).group(0)


def _checked(html, value):
    tag = re.search(rf'<input type="radio" name="choice" value="{value}"[^>]*>', html).group(0)
    return " checked" in tag


# Ansicht ---------------------------------------------------------------------------------


def test_the_colors_section_offers_an_edit_link_to_the_own_person_only(gated_client, alex, jamie):
    gated_client.force_login(alex.user)

    own = gated_client.get("/u/alex/").content.decode()
    foreign = gated_client.get("/u/jamie/").content.decode()

    assert 'href="/u/alex/edit/colors/"' in own
    assert 'hx-select="#profile-colors"' in own
    assert "/edit/colors/" not in foreign


def test_the_form_lists_each_test_result_as_a_radio_with_date_points_and_combination(
    gated_client, alex
):
    result = _result(alex)
    ColorCombination.objects.filter(code="WU", locale="en").update(name="Azorius")
    gated_client.force_login(alex.user)

    form = _form(gated_client.get(URL).content.decode())

    assert f'name="choice" value="{result.pk}"' in form
    assert "Azorius" in form
    assert "W: 9, U: 10, B: 6, R: 2, G: 3" in form
    assert result.taken_at.strftime("%Y") in form
    assert 'name="choice" value="manual"' in form


def test_the_form_points_to_the_test_when_there_is_no_result_yet(gated_client, alex):
    gated_client.force_login(alex.user)

    form = _form(gated_client.get(URL).content.decode())

    assert "haven't taken the test" in form
    assert 'href="/quiz/"' in form
    assert 'name="choice" value="manual"' in form


def test_the_adopted_result_is_preselected_and_marked(gated_client, alex):
    adopted = _result(alex)
    other = _result(alex, colors="BR")
    _assign(alex, "WU", adopted)
    gated_client.force_login(alex.user)

    html = gated_client.get(URL).content.decode()

    assert _checked(html, adopted.pk)
    assert not _checked(html, other.pk)
    assert not _checked(html, "manual")
    assert "shown in profile" in html


def test_manual_is_preselected_when_the_colors_were_chosen_by_hand(gated_client, alex):
    _result(alex)
    _assign(alex, "BR")
    gated_client.force_login(alex.user)

    html = gated_client.get(URL).content.decode()

    assert _checked(html, "manual")


def test_the_current_colors_are_prechecked(gated_client, alex):
    _assign(alex, "UB")
    gated_client.force_login(alex.user)

    form = _form(gated_client.get(URL).content.decode())

    checked = re.findall(r'<input type="checkbox" name="colors" value="(\w)"[^>]* checked', form)
    assert sorted(checked) == ["B", "U"]


# Fünfeck als Bedienhilfe ------------------------------------------------------------------


def test_the_form_contains_the_five_real_checkboxes_for_use_without_javascript(gated_client, alex):
    gated_client.force_login(alex.user)

    form = _form(gated_client.get(URL).content.decode())

    assert sorted(re.findall(r'<input type="checkbox" name="colors" value="(\w)"', form)) == [
        "B",
        "G",
        "R",
        "U",
        "W",
    ]


def test_the_pentagon_has_one_keyboard_operable_checkbox_per_color(gated_client, alex):
    _assign(alex, "UB")
    gated_client.force_login(alex.user)

    form = _form(gated_client.get(URL).content.decode())
    vertices = re.findall(r'<g class="pentagon__vertex color-field__vertex[^"]*"[^>]*>', form)

    assert len(vertices) == 5
    assert all('role="checkbox"' in v and 'tabindex="0"' in v for v in vertices)
    states = {
        re.search(r'data-color="(\w)"', v).group(1): 'aria-checked="true"' in v for v in vertices
    }
    assert states == {"W": False, "U": True, "B": True, "R": False, "G": False}


def test_the_pentagon_uses_the_same_geometry_as_the_color_wheel(gated_client, alex):
    from apps.colors import pentagon

    gated_client.force_login(alex.user)
    html = gated_client.get(URL).content.decode()
    vertices = pentagon.vertices(Color.objects.all())

    assert f'points="{pentagon.outline_points(vertices)}"' in html
    assert f'points="{pentagon.star_points(vertices)}"' in html
    assert f'viewBox="{pentagon.view_box(vertices)}"' in html


def test_the_script_is_loaded_on_the_profile_page(gated_client, alex):
    gated_client.force_login(alex.user)

    html = gated_client.get("/u/alex/").content.decode()

    assert "js/profile_colors.js" in html


def test_the_script_stays_small_and_free_of_frameworks():
    from django.conf import settings

    script = (settings.BASE_DIR / "static" / "js" / "profile_colors.js").read_text(encoding="utf-8")

    assert len(script.splitlines()) < 80
    assert "import " not in script


# Speichern: Testergebnis ----------------------------------------------------------------------


def test_choosing_a_test_result_links_it_and_shows_its_points(gated_client, alex, jamie):
    result = _result(alex, colors="WU", scores={"W": 9, "U": 10, "B": 6, "R": 2, "G": 3})
    _assign(alex, "BR")
    gated_client.force_login(alex.user)

    response = gated_client.post(URL, {"choice": str(result.pk), "colors": ["B", "R"]})

    assert response.status_code == 302
    assert response.url == "/u/alex/"
    assignment = ColorAssignment.objects.get(profile=alex)
    assert assignment.source == ColorAssignment.Source.SELF_TEST
    assert assignment.test_result == result
    assert assignment.combination.code == "WU"

    gated_client.force_login(jamie.user)
    html = gated_client.get("/u/alex/").content.decode()
    assert _bars(html) == {"W": 9, "U": 10, "B": 6, "R": 2, "G": 3}


def test_the_chosen_result_wins_over_the_checkboxes(gated_client, alex):
    result = _result(alex, colors="WU")
    gated_client.force_login(alex.user)

    gated_client.post(URL, {"choice": str(result.pk), "colors": ["G"]})

    assert ColorAssignment.objects.get(profile=alex).combination.code == "WU"


def test_a_result_of_someone_else_cannot_be_chosen(gated_client, alex, jamie):
    foreign = _result(jamie, colors="RG")
    gated_client.force_login(alex.user)

    response = gated_client.post(URL, {"choice": str(foreign.pk), "colors": []})

    assert response.status_code == 200
    assert "Choose one of your test results" in response.content.decode()
    assert not ColorAssignment.objects.filter(profile=alex).exists()


@pytest.mark.parametrize("choice", ["abc", "-1", "999999", "1; drop"])
def test_an_invalid_choice_is_rejected_and_nothing_changes(gated_client, alex, choice):
    _assign(alex, "WU")
    gated_client.force_login(alex.user)

    response = gated_client.post(URL, {"choice": choice, "colors": ["B"]})

    assert response.status_code == 200
    assert ColorAssignment.objects.get(profile=alex).combination.code == "WU"


# Speichern: manuell -------------------------------------------------------------------------------


def test_the_manual_choice_sets_manual_and_clears_the_reference_on_a_real_change(
    gated_client, alex
):
    result = _result(alex)
    _assign(alex, "WU", result)
    gated_client.force_login(alex.user)

    gated_client.post(URL, {"choice": "manual", "colors": ["W", "U", "B"]})

    assignment = ColorAssignment.objects.get(profile=alex)
    assert assignment.combination.code == "WUB"
    assert assignment.source == ColorAssignment.Source.SELF_MANUAL
    assert assignment.test_result is None


def test_the_unchanged_manual_choice_keeps_the_test_link(gated_client, alex):
    """D-72: wer das Formular ohne Änderung abschickt, verliert die Verknüpfung nicht."""
    result = _result(alex)
    _assign(alex, "WU", result)
    gated_client.force_login(alex.user)

    gated_client.post(URL, {"choice": "manual", "colors": ["U", "W"]})

    assert ColorAssignment.objects.get(profile=alex).test_result == result


def test_no_colors_clears_the_assignment(gated_client, alex):
    _assign(alex, "WU")
    gated_client.force_login(alex.user)

    gated_client.post(URL, {"choice": "manual"})

    assert not ColorAssignment.objects.filter(profile=alex).exists()


def test_a_missing_choice_counts_as_manual(gated_client, alex):
    gated_client.force_login(alex.user)

    gated_client.post(URL, {"colors": ["R", "G"]})

    assert ColorAssignment.objects.get(profile=alex).combination.code == "RG"


def test_an_unknown_color_letter_is_rejected(gated_client, alex):
    gated_client.force_login(alex.user)

    response = gated_client.post(URL, {"choice": "manual", "colors": ["X"]})

    assert response.status_code == 200
    assert not ColorAssignment.objects.filter(profile=alex).exists()


def test_saving_the_colors_changes_the_banner_and_the_combination_in_the_header(gated_client, alex):
    gated_client.force_login(alex.user)

    gated_client.post(URL, {"choice": "manual", "colors": ["U", "B"]})
    html = gated_client.get("/u/alex/").content.decode()

    assert 'href="/colors/ub/"' in html
    assert html.count("profile-banner__stripe") - html.count("profile-banner__stripe--neutral") == 2


# Nur die eigene Person ---------------------------------------------------------------------


def test_another_person_is_redirected_and_cannot_change_the_colors(gated_client, alex, jamie):
    gated_client.force_login(alex.user)

    get = gated_client.get("/u/jamie/edit/colors/")
    post = gated_client.post("/u/jamie/edit/colors/", {"choice": "manual", "colors": ["W"]})

    assert get.status_code == post.status_code == 302
    assert get.url == post.url == "/u/jamie/"
    assert not ColorAssignment.objects.filter(profile=jamie).exists()


def test_guests_are_sent_to_the_login(gated_client, jamie):
    response = gated_client.post("/u/jamie/edit/colors/", {"colors": ["W"]})

    assert response.status_code == 302
    assert "/accounts/login/" in response.url


# Übernahme von Historie und Ergebnisseite nutzt dieselbe Logik ----------------------------


def test_adopting_from_the_history_uses_the_same_code_path(gated_client, alex):
    result = _result(alex, colors="WU")
    gated_client.force_login(alex.user)

    gated_client.post(f"/quiz/results/{result.pk}/adopt/")

    assignment = ColorAssignment.objects.get(profile=alex)
    assert assignment.test_result == result
    assert assignment.source == ColorAssignment.Source.SELF_TEST
