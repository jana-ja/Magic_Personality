"""
Tests für das Pinnen und Lösen (Task 7.1, FR-B21, D-82).

Die Pinnwand selbst (Task 7.2) und das Ausblenden gelöschter/unsichtbarer
Ziele beim Anzeigen (Task 7.3, FR-B23) kommen mit den eigenen Tasks; hier
geht es um `Pin` selbst: anlegen, lösen, die Datenbank-Constraints und die
Kaskade beim Löschen von Beitrag oder Profil.
"""

import pytest
from django.db import IntegrityError, transaction

from apps.posts.comments import create_comment, make_tombstone
from apps.posts.models import Comment, Pin, Post, PostQuerySet
from apps.posts.pins import toggle_comment_pin, toggle_post_pin

pytestmark = pytest.mark.django_db

HTMX = {"HTTP_HX_REQUEST": "true"}


@pytest.fixture
def robin(make_profile):
    return make_profile("robin")


@pytest.fixture
def post(author):
    return Post.objects.create(author=author, title="The Post", body="b")


@pytest.fixture
def comment(post, author):
    return create_comment(post=post, author=author, body="Original comment")


@pytest.fixture
def member(gated_client, author):
    gated_client.force_login(author.user)
    return gated_client


def _pin_url(post):
    return f"/posts/{post.pk}/pin/"


def _comment_pin_url(post, comment):
    return f"/posts/{post.pk}/comments/{comment.pk}/pin/"


# Dienst (apps.posts.pins) ----------------------------------------------------------------


def test_toggle_post_pin_creates_and_then_removes_a_pin(author, post):
    assert toggle_post_pin(author, post) is True
    assert Pin.objects.filter(profile=author, post=post).exists()

    assert toggle_post_pin(author, post) is False
    assert not Pin.objects.filter(profile=author, post=post).exists()


def test_toggle_comment_pin_creates_and_then_removes_a_pin(author, comment):
    assert toggle_comment_pin(author, comment) is True
    assert Pin.objects.filter(profile=author, comment=comment).exists()

    assert toggle_comment_pin(author, comment) is False
    assert not Pin.objects.filter(profile=author, comment=comment).exists()


def test_pinning_ones_own_and_a_foreign_post_both_work(author, robin, post):
    """FR-B21/FR-B24: anders als beim Melden geht Pinnen bei eigenen **und**
    fremden Inhalten."""
    foreign = Post.objects.create(author=robin, title="Robin's post", body="b")

    assert toggle_post_pin(author, post) is True  # eigener Beitrag
    assert toggle_post_pin(author, foreign) is True  # fremder Beitrag
    assert Pin.objects.count() == 2


# Datenbank-Constraints (wie bei Report, D-81) ---------------------------------------------


def test_the_database_allows_one_pin_per_person_and_post(author, post):
    Pin.objects.create(profile=author, post=post)

    with pytest.raises(IntegrityError), transaction.atomic():
        Pin.objects.create(profile=author, post=post)


def test_the_database_allows_one_pin_per_person_and_comment(author, comment):
    Pin.objects.create(profile=author, comment=comment)

    with pytest.raises(IntegrityError), transaction.atomic():
        Pin.objects.create(profile=author, comment=comment)


def test_the_database_requires_exactly_one_target(author, post, comment):
    with pytest.raises(IntegrityError), transaction.atomic():
        Pin.objects.create(profile=author, post=post, comment=comment)

    with pytest.raises(IntegrityError), transaction.atomic():
        Pin.objects.create(profile=author)


def test_different_people_can_pin_the_same_post(author, robin, post):
    Pin.objects.create(profile=author, post=post)
    Pin.objects.create(profile=robin, post=post)

    assert Pin.objects.filter(post=post).count() == 2


# Views: Beitrag ----------------------------------------------------------------------------


def test_pinning_a_post_via_the_view_redirects_to_the_post(member, post):
    response = member.post(_pin_url(post))

    assert response.status_code == 302
    assert response.url == f"/posts/{post.pk}/"
    assert Pin.objects.filter(post=post).exists()


def test_pinning_twice_via_the_view_unpins(member, post):
    member.post(_pin_url(post))

    member.post(_pin_url(post))

    assert not Pin.objects.filter(post=post).exists()


def test_htmx_returns_only_the_pin_button(member, post):
    html = member.post(_pin_url(post), **HTMX).content.decode()

    assert html.strip().startswith('<span id="post-pin"')
    assert "Unpin" in html
    assert "<article" not in html  # nicht die ganze Seite


def test_the_button_label_switches_between_pin_and_unpin(member, post):
    before = member.get(f"/posts/{post.pk}/").content.decode()
    member.post(_pin_url(post))
    after = member.get(f"/posts/{post.pk}/").content.decode()

    assert "Unpin" not in before
    assert "Unpin" in after


def test_pinning_an_invisible_post_is_404(member, post, monkeypatch):
    monkeypatch.setattr(PostQuerySet, "visible_to", lambda self, profile: self.none())

    response = member.post(_pin_url(post))

    assert response.status_code == 404
    assert not Pin.objects.exists()


def test_only_post_is_allowed(member, post):
    assert member.get(_pin_url(post)).status_code == 405


# Views: Kommentar ----------------------------------------------------------------------------


def test_pinning_a_comment_via_the_view_redirects_to_its_anchor(member, post, comment):
    response = member.post(_comment_pin_url(post, comment))

    assert response.status_code == 302
    assert response.url == f"/posts/{post.pk}/#c-{comment.number}"
    assert Pin.objects.filter(comment=comment).exists()


def test_pinning_a_comment_twice_via_the_view_unpins(member, post, comment):
    member.post(_comment_pin_url(post, comment))

    member.post(_comment_pin_url(post, comment))

    assert not Pin.objects.filter(comment=comment).exists()


def test_htmx_returns_only_the_comments_pin_button(member, post, comment):
    html = member.post(_comment_pin_url(post, comment), **HTMX).content.decode()

    assert html.strip().startswith(f'<span id="comment-pin-{comment.pk}"')
    assert "Unpin" in html


def test_pinning_a_tombstoned_comment_does_nothing(member, post, comment):
    make_tombstone(comment)

    response = member.post(_comment_pin_url(post, comment))

    assert response.status_code == 302
    assert response.url == f"/posts/{post.pk}/"
    assert not Pin.objects.exists()


def test_pinning_a_comment_under_an_invisible_post_is_404(member, post, comment, monkeypatch):
    monkeypatch.setattr(PostQuerySet, "visible_to", lambda self, profile: self.none())

    response = member.post(_comment_pin_url(post, comment))

    assert response.status_code == 404
    assert not Pin.objects.exists()


def test_a_comment_of_a_different_post_is_404(member, post, author):
    other_post = Post.objects.create(author=author, title="Other", body="b")
    foreign_comment = create_comment(post=other_post, author=author, body="elsewhere")

    response = member.post(_comment_pin_url(post, foreign_comment))

    assert response.status_code == 404


def test_only_post_is_allowed_for_comments(member, post, comment):
    assert member.get(_comment_pin_url(post, comment)).status_code == 405


# Zugriffsschutz (zusätzlich zur Matrix in test_access_control.py) --------------------------


def test_pinning_needs_a_login(gated_client, post):
    response = gated_client.post(_pin_url(post))

    assert response.status_code == 302
    assert response.url.startswith("/accounts/login/")
    assert not Pin.objects.exists()


# Kaskade -------------------------------------------------------------------------------------


def test_deleting_the_post_removes_its_pins(author, post):
    Pin.objects.create(profile=author, post=post)

    post.delete()

    assert Pin.objects.count() == 0


def test_deleting_a_comment_via_post_deletion_removes_its_pins(author, post, comment):
    """Kommentare werden im Anwendungscode nie hart gelöscht (D-79), nur mit
    dem ganzen Beitrag kaskadiert (`Comment.post`, `on_delete=CASCADE`) —
    das nimmt auch die Pins auf ihn mit."""
    Pin.objects.create(profile=author, comment=comment)

    post.delete()

    assert Pin.objects.count() == 0
    assert not Comment.objects.filter(pk=comment.pk).exists()


def test_deleting_the_pinning_persons_account_removes_their_pins(author, robin, post):
    theirs = Post.objects.create(author=robin, title="Robin's post", body="b")
    Pin.objects.create(profile=author, post=theirs)

    author.user.delete()

    assert Pin.objects.count() == 0
    assert Post.objects.filter(pk=theirs.pk).exists()  # der Beitrag selbst bleibt


def test_deleting_the_pinned_posts_authors_account_removes_the_pin(author, robin, post):
    """Löscht die Autorin bzw. der Autor des Beitrags den eigenen Account, geht
    der Beitrag mit ihm (D-78) — und damit auch jeder Pin darauf, auch von
    einer anderen Person."""
    Pin.objects.create(profile=robin, post=post)

    author.user.delete()

    assert Pin.objects.count() == 0
