"""
Tests für das Beitragsmodell (Task 5.1, FR-B1, FR-B2, FR-B8, FR-B9, D-78).

Jede Regel wird zweimal geprüft: über `full_clean()` (das nutzen Formulare)
und über die Datenbank (schützt vor allem, was `full_clean()` umgeht).
"""

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from apps.posts.models import BODY_MAX_LENGTH, TITLE_MAX_LENGTH, Post

pytestmark = pytest.mark.django_db


def _post(author, **overrides):
    values = {"author": author, "title": "Thoughts on White-Green", "body": "Some text."}
    values.update(overrides)
    return Post(**values)


# Grundzustand ---------------------------------------------------------------


def test_a_new_post_is_public_general_and_unedited(author):
    post = Post.objects.create(author=author, title="Hello", body="Body")

    assert post.visibility == Post.Visibility.PUBLIC
    assert post.colors == ""
    assert post.edited_at is None
    assert post.comment_seq == 0
    assert post.created_at is not None


def test_a_post_belongs_to_a_profile_not_to_a_user(author):
    post = Post.objects.create(author=author, title="Hello", body="Body")

    assert post.author == author
    assert list(author.posts.all()) == [post]
    relations = {
        field.name: field.related_model._meta.label
        for field in Post._meta.fields
        if field.is_relation
    }
    assert relations == {"author": "accounts.Profile"}


def test_str_is_the_title(author):
    assert str(_post(author, title="A title")) == "A title"


# Farbcode -------------------------------------------------------------------


@pytest.mark.parametrize("code", ["", "W", "G", "WG", "UBR", "WUBRG"])
def test_canonical_color_codes_are_accepted(author, code):
    post = _post(author, colors=code)

    post.full_clean()
    post.save()

    assert Post.objects.get(pk=post.pk).colors == code


@pytest.mark.parametrize("code", ["GW", "WW", "X", "wg", "WGX", "WUBRGW", "W G"])
def test_non_canonical_color_codes_are_rejected_by_validation(author, code):
    with pytest.raises(ValidationError) as error:
        _post(author, colors=code).full_clean()

    assert "colors" in error.value.message_dict


@pytest.mark.parametrize("code", ["GW", "WW", "X", "wg", "WGX"])
def test_non_canonical_color_codes_are_rejected_by_the_database(author, code):
    with pytest.raises(IntegrityError), transaction.atomic():
        Post.objects.create(author=author, title="t", body="b", colors=code)


# Titel und Text -------------------------------------------------------------


def test_empty_title_is_rejected_by_validation_and_database(author):
    with pytest.raises(ValidationError) as error:
        _post(author, title="").full_clean()
    assert "title" in error.value.message_dict

    with pytest.raises(IntegrityError), transaction.atomic():
        Post.objects.create(author=author, title="", body="b")


def test_title_at_the_limit_is_accepted_and_beyond_is_rejected(author):
    _post(author, title="x" * TITLE_MAX_LENGTH).full_clean()

    with pytest.raises(ValidationError) as error:
        _post(author, title="x" * (TITLE_MAX_LENGTH + 1)).full_clean()
    assert "title" in error.value.message_dict


def test_body_at_the_limit_is_accepted_and_beyond_is_rejected(author):
    post = _post(author, body="x" * BODY_MAX_LENGTH)
    post.full_clean()
    post.save()

    with pytest.raises(ValidationError) as error:
        _post(author, body="x" * (BODY_MAX_LENGTH + 1)).full_clean()
    assert "body" in error.value.message_dict


def test_overlong_body_is_rejected_by_the_database(author):
    with pytest.raises(IntegrityError), transaction.atomic():
        Post.objects.create(author=author, title="t", body="x" * (BODY_MAX_LENGTH + 1))


# Sichtbarkeit (FR-B8, FR-B9) -------------------------------------------------


def test_visible_to_returns_public_posts(author, make_profile):
    post = Post.objects.create(author=author, title="Public", body="b")
    reader = make_profile("robin")

    assert list(Post.objects.visible_to(reader)) == [post]
    assert list(Post.objects.visible_to(author)) == [post]


def test_a_guest_sees_nothing(author):
    Post.objects.create(author=author, title="Public", body="b")

    assert list(Post.objects.visible_to(None)) == []


def test_visible_to_is_the_only_gate_and_excludes_anything_that_is_not_public(author, make_profile):
    """`friends` gibt es noch nicht — aber ein Wert, den kein Code kennt,
    darf nie durchrutschen. So bleibt die Regel auch dann dicht, wenn ein
    späterer Wert versehentlich vor `visible_to` gespeichert würde."""
    public = Post.objects.create(author=author, title="Public", body="b")
    Post.objects.create(author=author, title="Other", body="b", visibility="friends")

    assert list(Post.objects.visible_to(make_profile("robin"))) == [public]


def test_visible_to_is_chainable(author, make_profile):
    Post.objects.create(author=author, title="WG", body="b", colors="WG")
    Post.objects.create(author=author, title="General", body="b")

    result = Post.objects.visible_to(make_profile("robin")).filter(colors="WG")

    assert [post.title for post in result] == ["WG"]


def test_only_public_is_a_visibility_choice_for_now():
    assert [value for value, _label in Post.Visibility.choices] == ["public"]


# Reihenfolge und Löschen --------------------------------------------------------


def test_posts_are_ordered_newest_first(author):
    first = Post.objects.create(author=author, title="First", body="b")
    second = Post.objects.create(author=author, title="Second", body="b")

    assert list(Post.objects.all()) == [second, first]


def test_deleting_the_account_removes_its_posts_and_only_those(author, make_profile):
    other = make_profile("robin")
    Post.objects.create(author=author, title="Mine", body="b")
    kept = Post.objects.create(author=other, title="Theirs", body="b")

    author.user.delete()

    assert list(Post.objects.all()) == [kept]
