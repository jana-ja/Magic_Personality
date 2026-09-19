"""
Tests für die Testhistorie im eigenen Profil (Task 2.12, FR-P6 bis
FR-P8, D-19).

Der wichtigste Fall steht wörtlich in der Definition of Done in
docs/ROADMAP.md: fremde Historie ist über keinen Pfad erreichbar.
"""

import pytest
from django.utils import timezone

from apps.accounts.models import ColorAssignment, Profile, User
from apps.colors.models import ColorCombination
from apps.quiz.models import TestResult

pytestmark = pytest.mark.django_db

PROFILE_URL = "/accounts/profile/"  # Speichern (POST); die Seite selbst ist PROFILE_PAGE
PROFILE_PAGE = "/u/alex/history/"


@pytest.fixture
def user():
    user = User.objects.create_user(email="alex@example.com", password="a-long-enough-password")
    Profile.objects.create(user=user, nickname="alex")
    return user


@pytest.fixture
def other_user():
    user = User.objects.create_user(email="jamie@example.com", password="a-long-enough-password")
    Profile.objects.create(user=user, nickname="jamie")
    return user


def _make_result(profile, *, result_colors="WU", scores=None):
    return TestResult.objects.create(
        profile=profile,
        questionnaire_version=1,
        scores=scores or {"W": 5, "U": 3, "B": 0, "R": 0, "G": 0},
        result_colors=result_colors,
    )


# FR-P6: Historie im eigenen Profil, mit Datum/Punkten/Ergebnis --------------


def test_profile_shows_the_own_test_history(gated_client, user):
    result = _make_result(user.profile)
    gated_client.force_login(user)

    response = gated_client.get(PROFILE_PAGE)

    html = response.content.decode()
    assert 'href="/colors/wu/"' in html
    assert timezone.localtime(result.taken_at).strftime("%Y-%m-%d") in html
    assert "W: 5" in html
    assert "U: 3" in html


def test_profile_without_any_test_yet_shows_no_history(gated_client, user):
    gated_client.force_login(user)

    response = gated_client.get(PROFILE_PAGE)

    html = response.content.decode()
    assert "haven" in html.lower()
    assert 'href="/quiz/"' in html


def test_history_lists_points_in_wubrg_order(gated_client, user):
    """jsonb sortiert die Schlüssel um (B, G, R, U, W); angezeigt wird
    trotzdem in der Reihenfolge des Farbrads."""
    _make_result(user.profile, scores={"B": 6, "G": 18, "R": 2, "U": 10, "W": 9})
    gated_client.force_login(user)

    html = gated_client.get(PROFILE_PAGE).content.decode()

    assert "W: 9, U: 10, B: 6, R: 2, G: 18" in html


def test_history_never_shows_someone_elses_results(gated_client, user, other_user):
    other_result = _make_result(other_user.profile, result_colors="BR")
    gated_client.force_login(user)

    response = gated_client.get(PROFILE_PAGE)

    html = response.content.decode()
    assert "jamie" not in html
    assert f"/accounts/history/{other_result.pk}/delete/" not in html


def test_profile_page_requires_login(gated_client):
    response = gated_client.get(PROFILE_PAGE)

    assert response.status_code == 302
    assert response.url.startswith("/accounts/login/")


# FR-P7: einzelne Einträge löschbar ------------------------------------------


def test_deleting_an_own_entry_removes_it(gated_client, user):
    result = _make_result(user.profile)
    gated_client.force_login(user)

    response = gated_client.post(f"/accounts/history/{result.pk}/delete/")

    assert response.status_code == 302
    assert not TestResult.objects.filter(pk=result.pk).exists()


def test_deleting_requires_login(gated_client, user):
    result = _make_result(user.profile)

    response = gated_client.post(f"/accounts/history/{result.pk}/delete/")

    assert response.status_code == 302
    assert response.url.startswith("/accounts/login/")
    assert TestResult.objects.filter(pk=result.pk).exists()


def test_deleting_only_accepts_post(gated_client, user):
    result = _make_result(user.profile)
    gated_client.force_login(user)

    response = gated_client.get(f"/accounts/history/{result.pk}/delete/")

    assert response.status_code == 405
    assert TestResult.objects.filter(pk=result.pk).exists()


def test_deleting_someone_elses_entry_is_rejected(gated_client, user, other_user):
    """Fremde Historie ist über keinen Pfad erreichbar — auch nicht zum
    Löschen über einen erratenen Primärschlüssel."""
    other_result = _make_result(other_user.profile)
    gated_client.force_login(user)

    response = gated_client.post(f"/accounts/history/{other_result.pk}/delete/")

    assert response.status_code == 404
    assert TestResult.objects.filter(pk=other_result.pk).exists()


# FR-P8: gelöschter Referenz-Eintrag leert nur die Referenz ------------------


def test_deleting_the_referenced_entry_clears_only_the_reference(gated_client, user):
    result = _make_result(user.profile, result_colors="WU")
    combination = ColorCombination.objects.get(code="WU", locale="en")
    assignment = ColorAssignment.objects.create(
        profile=user.profile,
        author_profile=user.profile,
        combination=combination,
        source=ColorAssignment.Source.SELF_TEST,
        test_result=result,
    )
    gated_client.force_login(user)

    gated_client.post(f"/accounts/history/{result.pk}/delete/")

    assignment.refresh_from_db()
    assert assignment.test_result is None
    assert assignment.combination == combination
    assert assignment.source == ColorAssignment.Source.SELF_TEST


def test_deleting_an_unreferenced_entry_leaves_the_color_assignment_untouched(gated_client, user):
    referenced = _make_result(user.profile, result_colors="WU")
    other = _make_result(user.profile, result_colors="B")
    combination = ColorCombination.objects.get(code="WU", locale="en")
    assignment = ColorAssignment.objects.create(
        profile=user.profile,
        author_profile=user.profile,
        combination=combination,
        source=ColorAssignment.Source.SELF_TEST,
        test_result=referenced,
    )
    gated_client.force_login(user)

    gated_client.post(f"/accounts/history/{other.pk}/delete/")

    assignment.refresh_from_db()
    assert assignment.test_result == referenced


# Nachträgliche Übernahme ins Profil aus der Historie ---------------------


def test_history_offers_to_adopt_a_result_into_the_profile(gated_client, user):
    result = _make_result(user.profile)
    gated_client.force_login(user)

    html = gated_client.get(PROFILE_PAGE).content.decode()

    assert f'action="/quiz/results/{result.pk}/adopt/"' in html
    assert "Use for profile" in html


def test_adopting_from_the_history_links_the_result_and_shows_its_scores_to_others(
    gated_client, user, other_user
):
    """Auch für Zuordnungen, die vorher manuell gesetzt wurden und die
    Testreferenz überschrieben hatten (FR-P5)."""
    result = _make_result(user.profile, scores={"W": 9, "U": 10, "B": 6, "R": 2, "G": 3})
    ColorAssignment.objects.create(
        profile=user.profile,
        author_profile=user.profile,
        combination=ColorCombination.objects.get(code="BR", locale="en"),
        source=ColorAssignment.Source.SELF_MANUAL,
    )
    gated_client.force_login(user)

    response = gated_client.post(f"/quiz/results/{result.pk}/adopt/")

    assert response.status_code == 302
    assignment = ColorAssignment.objects.get(profile=user.profile)
    assert assignment.source == ColorAssignment.Source.SELF_TEST
    assert assignment.test_result == result
    assert assignment.combination.code == "WU"

    gated_client.force_login(other_user)
    html = gated_client.get("/u/alex/").content.decode()
    assert "W: 9, U: 10, B: 6, R: 2, G: 3" in html


def test_the_currently_adopted_result_shows_a_note_instead_of_the_button(gated_client, user):
    adopted = _make_result(user.profile)
    other = _make_result(user.profile, result_colors="BR")
    ColorAssignment.objects.create(
        profile=user.profile,
        author_profile=user.profile,
        combination=ColorCombination.objects.get(code="WU", locale="en"),
        source=ColorAssignment.Source.SELF_TEST,
        test_result=adopted,
    )
    gated_client.force_login(user)

    html = gated_client.get(PROFILE_PAGE).content.decode()

    assert "Shown in profile" in html
    assert f'action="/quiz/results/{adopted.pk}/adopt/"' not in html
    assert f'action="/quiz/results/{other.pk}/adopt/"' in html
