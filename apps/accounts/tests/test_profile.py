"""
Tests für `Profile` und `ColorAssignment` (Task 2.1).

Der Fall aus der Definition of Done in docs/ROADMAP.md steht zuerst
wörtlich drin: zwei Profile mit "Alice" und "alice" dürfen nicht
gleichzeitig existieren (FR-P2).
"""

import pytest
from django.db.utils import IntegrityError

from apps.accounts.models import ColorAssignment, Profile, User
from apps.colors.models import ColorCombination
from apps.quiz.models import TestResult

pytestmark = pytest.mark.django_db


def test_two_profiles_with_case_variant_nicknames_cannot_coexist():
    Profile.objects.create(nickname="Alice")

    with pytest.raises(IntegrityError):
        Profile.objects.create(nickname="alice")


def test_profile_user_is_optional():
    profile = Profile.objects.create(nickname="ghost")

    assert profile.user is None


def test_profile_can_be_linked_to_a_user():
    user = User.objects.create_user(email="alex@example.com", password="a-long-enough-password")
    profile = Profile.objects.create(nickname="alex", user=user)

    assert profile.user == user
    assert user.profile == profile


def _wu_combination():
    return ColorCombination.objects.get(code="WU", locale="en")


def test_at_most_one_color_assignment_per_profile():
    profile = Profile.objects.create(nickname="alex")
    combination = _wu_combination()
    ColorAssignment.objects.create(
        profile=profile,
        author_profile=profile,
        combination=combination,
        source=ColorAssignment.Source.SELF_MANUAL,
    )

    with pytest.raises(IntegrityError):
        ColorAssignment.objects.create(
            profile=profile,
            author_profile=profile,
            combination=combination,
            source=ColorAssignment.Source.SELF_MANUAL,
        )


def test_color_assignment_from_a_test_result_keeps_the_reference():
    profile = Profile.objects.create(nickname="alex")
    result = TestResult.objects.create(
        profile=profile,
        questionnaire_version=1,
        scores={"W": 5, "U": 3, "B": 4, "R": 4, "G": 4},
        result_colors="WU",
    )

    assignment = ColorAssignment.objects.create(
        profile=profile,
        author_profile=profile,
        combination=_wu_combination(),
        source=ColorAssignment.Source.SELF_TEST,
        test_result=result,
    )

    assert assignment.test_result == result


def test_deleting_the_referenced_test_result_clears_the_reference_only():
    """FR-P8: die Farben bleiben bestehen, nur die Referenz wird leer."""
    profile = Profile.objects.create(nickname="alex")
    result = TestResult.objects.create(
        profile=profile,
        questionnaire_version=1,
        scores={"W": 5, "U": 3, "B": 4, "R": 4, "G": 4},
        result_colors="WU",
    )
    assignment = ColorAssignment.objects.create(
        profile=profile,
        author_profile=profile,
        combination=_wu_combination(),
        source=ColorAssignment.Source.SELF_TEST,
        test_result=result,
    )

    result.delete()
    assignment.refresh_from_db()

    assert assignment.test_result is None
    assert assignment.combination == _wu_combination()
