"""
Tests für das Kommentarmodell und die Nummernvergabe (Task 6.1, FR-B14,
FR-B15, D-79).

`create_comment()` (`apps.posts.comments`) ist die einzige Stelle, die
Kommentare anlegt — dieselbe Erwartung wie bei `Post.objects.visible_to()`
(Task 5.9), hier aber (noch) ohne eigenen Wächtertest: Task 6.2 baut die
Views darauf auf und kann dabei dieselbe Prüfung wie in
`test_architecture.py` bekommen.
"""

import threading

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, connection, transaction
from django.db.models.deletion import ProtectedError
from django.utils import timezone

from apps.posts.comments import create_comment
from apps.posts.models import COMMENT_MAX_LENGTH, Comment, Post

pytestmark = pytest.mark.django_db


@pytest.fixture
def post(author):
    return Post.objects.create(author=author, title="Original", body="Original text")


# Nummernvergabe --------------------------------------------------------------------


def test_the_first_comment_gets_number_one(post, author):
    comment = create_comment(post=post, author=author, body="First!")

    assert comment.number == 1
    assert comment.post == post
    assert comment.author == author
    assert comment.body == "First!"
    assert comment.reply_to is None
    assert comment.deleted_at is None
    assert not comment.is_tombstone


def test_numbers_count_up_per_post(post, author):
    first = create_comment(post=post, author=author, body="one")
    second = create_comment(post=post, author=author, body="two")
    third = create_comment(post=post, author=author, body="three")

    assert (first.number, second.number, third.number) == (1, 2, 3)


def test_each_post_counts_its_own_numbers(author):
    post_a = Post.objects.create(author=author, title="A", body="b")
    post_b = Post.objects.create(author=author, title="B", body="b")

    create_comment(post=post_a, author=author, body="a1")
    b1 = create_comment(post=post_b, author=author, body="b1")
    a2 = create_comment(post=post_a, author=author, body="a2")

    assert (b1.number, a2.number) == (1, 2)


def test_the_posts_counter_advances_with_each_comment(post, author):
    create_comment(post=post, author=author, body="one")
    create_comment(post=post, author=author, body="two")

    post.refresh_from_db()
    assert post.comment_seq == 2


def test_deleting_a_comment_row_never_frees_its_number(post, author):
    """Steht für die spätere Hülle (Task 6.3): die Nummer kommt aus dem
    Zähler, nicht aus der Zahl vorhandener Zeilen — ein hartes Löschen
    (hier zum Nachstellen benutzt, im Anwendungscode kommt das nicht vor)
    hinterlässt deshalb eine Lücke statt einer Wiederverwendung."""
    first = create_comment(post=post, author=author, body="one")
    second = create_comment(post=post, author=author, body="two")
    second.delete()

    third = create_comment(post=post, author=author, body="three")

    assert (first.number, third.number) == (1, 3)


@pytest.mark.django_db(transaction=True)
def test_concurrent_comments_never_collide_on_a_number(author, make_profile):
    """`select_for_update()` serialisiert gleichzeitige Anfragen zu
    **demselben** Beitrag (D-79): jeder von zwölf Threads, gemeinsam
    losgelassen durch eine `Barrier`, bekommt eine eigene, fortlaufende
    Nummer — keine doppelt, keine Lücke."""
    thread_count = 12
    post = Post.objects.create(author=author, title="T", body="b")
    commenters = [make_profile(f"racer{i}") for i in range(thread_count)]
    numbers = [None] * thread_count
    errors = []
    barrier = threading.Barrier(thread_count)

    def worker(index):
        try:
            barrier.wait(timeout=5)
            comment = create_comment(post=post, author=commenters[index], body=f"c{index}")
            numbers[index] = comment.number
        except Exception as error:  # noqa: BLE001 - surfaced below, not swallowed
            errors.append(error)
        finally:
            connection.close()

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(thread_count)]
    for started in threads:
        started.start()
    for finished in threads:
        finished.join()

    assert errors == []
    assert sorted(numbers) == list(range(1, thread_count + 1))
    post.refresh_from_db()
    assert post.comment_seq == thread_count


# Antworten (reply_to, FR-B15) --------------------------------------------------------


def test_a_comment_can_reply_to_an_earlier_one(post, author):
    first = create_comment(post=post, author=author, body="one")

    reply = create_comment(post=post, author=author, body="re: one", reply_to=first)

    assert reply.reply_to == first
    assert reply.number == 2


def test_a_reply_to_a_different_posts_comment_is_rejected(author):
    post_a = Post.objects.create(author=author, title="A", body="b")
    post_b = Post.objects.create(author=author, title="B", body="b")
    foreign = create_comment(post=post_a, author=author, body="over there")

    with pytest.raises(ValidationError):
        create_comment(post=post_b, author=author, body="reply", reply_to=foreign)

    assert Comment.objects.filter(post=post_b).count() == 0
    post_b.refresh_from_db()
    assert post_b.comment_seq == 0  # kein Versuch hat den Zähler berührt


def test_replying_to_a_tombstone_is_rejected(post, author):
    """Task 6.1 legt noch keinen Löschweg an — die Hülle wird hier direkt
    nachgestellt, wie es Task 6.3s Dienst später herstellen wird."""
    tombstone = create_comment(post=post, author=author, body="soon deleted")
    tombstone.deleted_at = timezone.now()
    tombstone.author = None
    tombstone.body = ""
    tombstone.save(update_fields=["deleted_at", "author", "body"])

    with pytest.raises(ValidationError):
        create_comment(post=post, author=author, body="too late", reply_to=tombstone)

    post.refresh_from_db()
    assert post.comment_seq == 1  # nur die Hülle selbst zählte


def test_a_post_that_is_not_visible_to_the_author_refuses_the_comment(post, author, monkeypatch):
    """Task 5.9s Wächter verlangt, dass jeder Lesezugriff auf `Post` durch
    `visible_to()` geht (FR-B9, D-78) — auch hier: die Sperre liest über
    `visible_to(author)`, nicht über `Post.objects` direkt."""
    from apps.posts.models import PostQuerySet

    monkeypatch.setattr(PostQuerySet, "visible_to", lambda self, profile: self.none())

    with pytest.raises(Post.DoesNotExist):
        create_comment(post=post, author=author, body="too late")

    assert Comment.objects.count() == 0


# Modell: Constraints und Grundzustand -------------------------------------------------


def test_str_names_the_number_and_the_post(post, author):
    comment = create_comment(post=post, author=author, body="hi")

    assert str(comment) == f"#1 on {post}"


def test_comments_are_ordered_by_number(post, author):
    third = Comment.objects.create(post=post, author=author, number=3, body="c")
    first = Comment.objects.create(post=post, author=author, number=1, body="a")
    second = Comment.objects.create(post=post, author=author, number=2, body="b")

    assert list(Comment.objects.filter(post=post)) == [first, second, third]


def test_the_database_refuses_two_comments_with_the_same_number(post, author):
    Comment.objects.create(post=post, author=author, number=1, body="a")

    with pytest.raises(IntegrityError), transaction.atomic():
        Comment.objects.create(post=post, author=author, number=1, body="b")


def test_the_same_number_is_fine_on_a_different_post(author):
    post_a = Post.objects.create(author=author, title="A", body="b")
    post_b = Post.objects.create(author=author, title="B", body="b")

    Comment.objects.create(post=post_a, author=author, number=1, body="a")
    Comment.objects.create(post=post_b, author=author, number=1, body="b")  # kein Fehler

    assert Comment.objects.count() == 2


def test_a_body_at_the_limit_is_accepted_and_beyond_is_rejected_by_validation(post, author):
    ok = Comment(post=post, author=author, number=1, body="x" * COMMENT_MAX_LENGTH)
    ok.full_clean()

    too_long = Comment(post=post, author=author, number=2, body="x" * (COMMENT_MAX_LENGTH + 1))
    with pytest.raises(ValidationError) as error:
        too_long.full_clean()
    assert "body" in error.value.message_dict


def test_an_overlong_body_is_rejected_by_the_database_too(post, author):
    with pytest.raises(IntegrityError), transaction.atomic():
        Comment.objects.create(
            post=post, author=author, number=1, body="x" * (COMMENT_MAX_LENGTH + 1)
        )


def test_a_tombstone_may_have_an_empty_body_and_no_author(post):
    """Die Datenbank erzwingt die Hülle nicht (kein Constraint über zwei
    Spalten hinweg) — sie lässt nur zu, dass `apps.posts.comments`s künftiger
    Löschweg (Task 6.3) sie herstellen kann."""
    tombstone = Comment.objects.create(
        post=post, author=None, number=1, body="", deleted_at=timezone.now()
    )

    assert tombstone.is_tombstone
    assert tombstone.author is None
    assert tombstone.body == ""


def test_deleting_the_post_removes_its_comments(post, author):
    create_comment(post=post, author=author, body="one")

    post.delete()

    assert Comment.objects.count() == 0


def test_hard_deleting_a_replied_to_comment_clears_the_reference_not_the_reply(post, author):
    """Betrifft nur ein hartes Löschen außerhalb des Anwendungscodes (wie beim
    Nummern-Test oben) — der eigentliche Löschweg (Task 6.3) tombstoned statt
    zu löschen. Dokumentiert trotzdem die gewählte `on_delete`-Regel für
    `reply_to`: die Antwort bleibt stehen, auch wenn ihr Bezug verschwindet,
    nur die Referenz wird leer."""
    original = create_comment(post=post, author=author, body="one")
    reply = create_comment(post=post, author=author, body="re: one", reply_to=original)

    original.delete()

    reply.refresh_from_db()
    assert reply.reply_to is None
    assert reply.number == 2


# Autor: on_delete=PROTECT (D-79) ------------------------------------------------------


def test_a_comments_author_cannot_be_cascaded_away(post, author):
    """Die Ausnahme von der sonst durchgängigen Kaskade (Task 5.9s Wächter
    kennt `Post`/`Report`, nicht `Comment`): Löscht jemand den eigenen Account,
    ohne die eigenen Kommentare vorher zur Hülle zu machen (Task 6.3), bricht
    das hier ab, statt eine Zeile mit Autor, aber ohne Profil zu hinterlassen."""
    create_comment(post=post, author=author, body="mine")

    with pytest.raises(ProtectedError):
        author.user.delete()

    assert Post.objects.filter(pk=post.pk).exists()


def test_once_the_authors_comments_have_no_author_left_the_account_can_be_deleted(post, author):
    comment = create_comment(post=post, author=author, body="mine")
    comment.author = None
    comment.save(update_fields=["author"])

    author.user.delete()  # löst nicht mehr aus

    assert not Post.objects.filter(pk=post.pk).exists()
    assert Comment.objects.count() == 0  # ging mit dem eigenen Beitrag (Post-Kaskade)


def test_a_comment_on_someone_elses_post_only_blocks_its_own_author(post, author, make_profile):
    stranger = make_profile("robin")
    create_comment(post=post, author=stranger, body="visiting")

    author.user.delete()  # die Autorin/der Autor des Beitrags hat selbst nichts kommentiert

    assert not Post.objects.filter(pk=post.pk).exists()
    assert Comment.objects.count() == 0  # ging mit dem Beitrag, unabhängig vom Autor des Kommentars
