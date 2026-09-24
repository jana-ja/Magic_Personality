"""
Tests für das Löschen von Kommentaren (Task 6.3, FR-B16, D-79).

`test_access_control.py` deckt Zugriff, CSRF und Methoden ab; hier geht es um
das eigentliche Verhalten: die Hülle selbst, ihre Sichtbarkeit mit und ohne
Antworten, und die Dienste `make_tombstone()`/`tombstone_comments_by()`.
"""

import re

import pytest

from apps.accounts.models import User
from apps.posts.comments import create_comment, make_tombstone, tombstone_comments_by
from apps.posts.models import Comment, Post, PostQuerySet

pytestmark = pytest.mark.django_db


@pytest.fixture
def member(gated_client, author):
    gated_client.force_login(author.user)
    return gated_client


@pytest.fixture
def post(author):
    return Post.objects.create(author=author, title="Original", body="Original text")


def delete_url(post, comment):
    return f"/posts/{post.pk}/comments/{comment.pk}/delete/"


def detail_url(post):
    return f"/posts/{post.pk}/"


def _comment_block(html, number):
    match = re.search(rf'<article id="c-{number}".*?</article>', html, re.S)
    return match.group(0) if match else ""


# Löschen durch die Autorin/den Autor (die View) --------------------------------------------


def test_a_get_shows_the_confirmation_and_changes_nothing(member, post, author):
    comment = create_comment(post=post, author=author, body="oops")

    response = member.get(delete_url(post, comment))

    assert response.status_code == 200
    assert "#1" in response.content.decode()
    comment.refresh_from_db()
    assert not comment.is_tombstone
    assert comment.body == "oops"


def test_a_post_tombstones_the_comment_and_redirects_to_the_post(member, post, author):
    comment = create_comment(post=post, author=author, body="oops")

    response = member.post(delete_url(post, comment))

    assert response.status_code == 302
    assert response.url == detail_url(post)
    comment.refresh_from_db()
    assert comment.is_tombstone
    assert comment.deleted_at is not None
    assert comment.author is None
    assert comment.body == ""


def test_the_number_and_reply_references_survive_deletion(member, post, author):
    first = create_comment(post=post, author=author, body="one")
    reply = create_comment(post=post, author=author, body="re: one", reply_to=first)

    member.post(delete_url(post, first))

    first.refresh_from_db()
    reply.refresh_from_db()
    assert first.number == 1  # unverändert
    assert reply.reply_to_id == first.pk  # der Verweis zeigt weiter auf dieselbe Zeile


def test_a_guest_is_sent_to_the_login_and_nothing_changes(gated_client, post, author):
    comment = create_comment(post=post, author=author, body="oops")

    response = gated_client.post(delete_url(post, comment))

    assert response.status_code == 302
    assert response.url.startswith("/accounts/login/")
    comment.refresh_from_db()
    assert not comment.is_tombstone


def test_a_mismatched_post_and_comment_is_404(member, post, author, make_profile):
    other_post = Post.objects.create(author=author, title="Other", body="b")
    comment = create_comment(post=other_post, author=author, body="over there")

    response = member.get(f"/posts/{post.pk}/comments/{comment.pk}/delete/")

    assert response.status_code == 404
    comment.refresh_from_db()
    assert not comment.is_tombstone


def test_an_unknown_comment_is_404(member, post):
    assert member.post(f"/posts/{post.pk}/comments/999999/delete/").status_code == 404


def test_a_post_that_is_not_visible_is_404(member, post, author, monkeypatch):
    comment = create_comment(post=post, author=author, body="oops")
    monkeypatch.setattr(PostQuerySet, "visible_to", lambda self, profile: self.none())

    response = member.post(delete_url(post, comment))

    assert response.status_code == 404
    comment.refresh_from_db()
    assert not comment.is_tombstone


def test_deleting_an_already_deleted_comment_changes_nothing_further(member, post, author):
    comment = create_comment(post=post, author=author, body="oops")
    make_tombstone(comment)
    first_deleted_at = comment.deleted_at

    response = member.post(delete_url(post, comment))

    assert response.status_code == 302  # "nicht mein Kommentar" (author ist None), keine 404
    comment.refresh_from_db()
    assert comment.deleted_at == first_deleted_at


# Sichtbarkeit auf der Beitragsseite -----------------------------------------------------------


def test_a_deleted_comment_without_replies_disappears_from_the_page(member, post, author):
    comment = create_comment(post=post, author=author, body="oops")

    member.post(delete_url(post, comment))
    html = member.get(detail_url(post)).content.decode()

    assert "0 comments" in html
    assert f'id="c-{comment.number}"' not in html


def test_a_deleted_comment_with_a_reply_stays_as_a_numbered_placeholder(member, post, author):
    original = create_comment(post=post, author=author, body="oops")
    create_comment(post=post, author=author, body="a reply", reply_to=original)

    member.post(delete_url(post, original))
    html = member.get(detail_url(post)).content.decode()

    block = _comment_block(html, original.number)
    assert block != ""
    assert "deleted" in block
    assert "oops" not in block
    assert "author-card" not in block
    assert "Reply" not in block
    assert "Delete" not in block
    assert "2 comments" in html  # die Hülle zählt mit, die Antwort auch


def test_delete_is_offered_only_to_the_comments_own_author(member, post, author, make_profile):
    stranger = make_profile("robin")
    own = create_comment(post=post, author=author, body="mine")
    foreign = create_comment(post=post, author=stranger, body="theirs")

    html = member.get(detail_url(post)).content.decode()

    assert delete_url(post, own) in html
    assert delete_url(post, foreign) not in html


# make_tombstone() -------------------------------------------------------------------------------


def test_make_tombstone_clears_body_and_author_and_sets_deleted_at(post, author):
    comment = create_comment(post=post, author=author, body="oops")

    result = make_tombstone(comment)

    assert result is comment
    assert comment.is_tombstone
    assert comment.author is None
    assert comment.body == ""
    assert comment.deleted_at is not None
    comment.refresh_from_db()  # tatsächlich gespeichert, nicht nur im Objekt geändert
    assert comment.is_tombstone and comment.author is None and comment.body == ""


def test_make_tombstone_on_an_existing_tombstone_is_a_harmless_no_op(post, author):
    comment = create_comment(post=post, author=author, body="oops")
    make_tombstone(comment)
    first_deleted_at = comment.deleted_at

    make_tombstone(comment)

    assert comment.deleted_at == first_deleted_at


def test_make_tombstone_does_not_touch_the_number_or_the_post(post, author):
    create_comment(post=post, author=author, body="one")
    second = create_comment(post=post, author=author, body="two")

    make_tombstone(second)

    assert second.number == 2
    assert second.post_id == post.pk


# tombstone_comments_by() (Vorarbeit für die Account-Löschung, FR-B19) --------------------------


def test_tombstone_comments_by_affects_only_that_persons_comments(post, author, make_profile):
    robin = make_profile("robin")
    mine = create_comment(post=post, author=author, body="mine")
    theirs = create_comment(post=post, author=robin, body="theirs")

    tombstone_comments_by(author)

    mine.refresh_from_db()
    theirs.refresh_from_db()
    assert mine.is_tombstone
    assert not theirs.is_tombstone
    assert theirs.author == robin


def test_tombstone_comments_by_covers_every_post_not_only_ones_the_person_wrote(
    post, author, make_profile
):
    someone_elses_post = Post.objects.create(author=make_profile("robin"), title="T", body="b")
    elsewhere = create_comment(post=someone_elses_post, author=author, body="visiting")

    tombstone_comments_by(author)

    elsewhere.refresh_from_db()
    assert elsewhere.is_tombstone


def test_tombstone_comments_by_is_a_single_bulk_update(django_assert_num_queries, post, author):
    for number in range(5):
        create_comment(post=post, author=author, body=f"c{number}")

    with django_assert_num_queries(1):
        tombstone_comments_by(author)


def test_tombstone_comments_by_on_a_person_with_no_comments_does_nothing(post, author):
    tombstone_comments_by(author)  # darf nicht crashen

    assert Comment.objects.count() == 0


# Kaskade der Architektur-Ausnahme (Task 5.9/6.1, D-79) ------------------------------------------


def test_deleting_the_profile_is_blocked_unless_comments_were_tombstoned_first(post, author):
    from django.db.models.deletion import ProtectedError

    create_comment(post=post, author=author, body="mine")
    user_id = author.user_id

    with pytest.raises(ProtectedError):
        author.user.delete()

    assert User.objects.filter(pk=user_id).exists()  # der Versuch brach ab, nichts ist weg

    tombstone_comments_by(author)
    author.user.delete()  # jetzt kein Fehler mehr

    assert not User.objects.filter(pk=user_id).exists()
