"""
Tests für Account-Löschung und Datenschutz mit Beiträgen (Task 5.8, FR-B12,
D-78, D-81), Kommentaren (Task 6.3, FR-B19, D-79) und Pins (Task 7.3,
FR-B23, D-82).

Die Kaskade selbst (Beitrag und Meldung verschwinden mit Profil bzw. Beitrag)
steht schon in test_models.py und test_reports.py, die Pin-Kaskade in
test_pins.py; hier geht es um den echten Weg über die View und um das, was
Nutzende darüber lesen.
"""

import pytest
from django.db import models

from apps.accounts.models import Profile, User
from apps.posts.comments import create_comment
from apps.posts.models import Comment, Pin, Post, PostSeen, Report

pytestmark = pytest.mark.django_db

DELETE_URL = "/accounts/delete/"


@pytest.fixture
def robin(make_profile):
    return make_profile("robin")


@pytest.fixture
def member(gated_client, author):
    gated_client.force_login(author.user)
    return gated_client


# Löschen über die View ------------------------------------------------------------------


def test_deleting_the_account_removes_posts_and_reports_of_the_person(member, author, robin):
    mine = Post.objects.create(author=author, title="Mine", body="b", colors="WG")
    theirs = Post.objects.create(author=robin, title="Theirs", body="b", colors="WG")
    sent = Report.objects.create(reporter=author, post=theirs, reason="spam")
    received = Report.objects.create(reporter=robin, post=mine, reason="also spam")

    member.post(DELETE_URL)

    assert not Post.objects.filter(pk=mine.pk).exists()
    assert not Report.objects.filter(pk=sent.pk).exists()  # gemeldet von der gelöschten Person
    assert not Report.objects.filter(pk=received.pk).exists()  # gemeldet wurde ihr Beitrag


def test_other_peoples_posts_and_their_profiles_stay(member, author, robin, make_profile):
    Post.objects.create(author=author, title="Mine", body="b")
    theirs = Post.objects.create(author=robin, title="Theirs", body="b")
    sams = Post.objects.create(author=make_profile("sam"), title="Sams", body="b")
    Report.objects.create(reporter=make_profile("kai"), post=theirs, reason="unrelated")

    member.post(DELETE_URL)

    assert set(Post.objects.all()) == {theirs, sams}
    assert Report.objects.count() == 1
    assert Profile.objects.filter(nickname="robin").exists()


def test_nothing_of_the_deleted_person_is_left_in_the_lists(member, author, robin):
    Post.objects.create(author=author, title="Gone soon", body="b", colors="WG")
    Post.objects.create(author=robin, title="Stays", body="b", colors="WG")
    member.post(DELETE_URL)
    member.force_login(robin.user)

    grid = member.get("/colors/wg/").content.decode()

    assert "Stays" in grid
    assert "Gone soon" not in grid
    assert member.get("/u/alex/posts/").status_code == 404


def test_the_deleted_posts_page_is_gone(member, author, robin):
    post = Post.objects.create(author=author, title="Gone soon", body="b")
    member.post(DELETE_URL)
    member.force_login(robin.user)

    assert member.get(f"/posts/{post.pk}/").status_code == 404


def test_every_relation_from_posts_to_a_person_deletes_with_the_person():
    """Beiträge, Meldungen, der Zähler-Stand und Pins gehören der Person: jeder
    Verweis der Posts-App auf ein Profil kaskadiert — mit **einer** bewussten,
    hier ausdrücklich benannten Ausnahme seit Task 6.3: `Comment.author`
    (D-79, `PROTECT`, weil ein Kommentar erst zur Hülle werden muss, siehe die
    Tests unten). `Pin` seit Task 7.1/7.3 mit aufgenommen — dieselbe Regel
    gilt für neue Modelle, ohne dass dieser Test von Hand daran erinnert
    werden müsste, sähe eine Änderung an `Pin.profile` sie nicht als bewusste
    Ausnahme aus."""
    exceptions = {(Comment, "author"): models.PROTECT}
    for model in (Post, Report, Comment, PostSeen, Pin):
        for field in model._meta.fields:
            if field.is_relation and field.related_model is Profile:
                expected = exceptions.get((model, field.name), models.CASCADE)
                assert field.remote_field.on_delete is expected, (model, field.name)


# Kommentare (Task 6.3, FR-B19, D-79) ------------------------------------------------------


def test_deleting_the_account_tombstones_comments_under_foreign_posts(member, author, robin):
    theirs = Post.objects.create(author=robin, title="Theirs", body="b")
    mine = create_comment(post=theirs, author=author, body="my two cents")
    someone_replied = create_comment(post=theirs, author=robin, body="re: you", reply_to=mine)

    member.post(DELETE_URL)

    mine.refresh_from_db()
    assert mine.is_tombstone
    assert mine.author is None
    assert mine.body == ""
    assert mine.number == 1  # die Nummer bleibt, der Verweis der Antwort auch
    someone_replied.refresh_from_db()
    assert someone_replied.reply_to_id == mine.pk


def test_a_tombstoned_comment_without_replies_disappears_from_the_page(member, author, robin):
    theirs = Post.objects.create(author=robin, title="Theirs", body="b")
    create_comment(post=theirs, author=author, body="my two cents")

    member.post(DELETE_URL)
    member.force_login(robin.user)

    html = member.get(f"/posts/{theirs.pk}/").content.decode()
    assert "0 comments" in html


def test_comments_under_the_deleted_persons_own_post_vanish_with_the_post(member, author, robin):
    mine = Post.objects.create(author=author, title="Mine", body="b")
    theirs_on_mine = create_comment(post=mine, author=robin, body="visiting")

    member.post(DELETE_URL)

    assert not Post.objects.filter(pk=mine.pk).exists()
    assert not Comment.objects.filter(pk=theirs_on_mine.pk).exists()


def test_other_peoples_comments_and_their_authorship_stay(member, author, robin, make_profile):
    post = Post.objects.create(author=make_profile("sam"), title="Sam's", body="b")
    theirs = create_comment(post=post, author=robin, body="staying")

    member.post(DELETE_URL)

    theirs.refresh_from_db()
    assert theirs.author == robin
    assert theirs.body == "staying"


# Pins (Task 7.1/7.3, FR-B21, FR-B23, D-82) -----------------------------------------------


def test_deleting_the_account_removes_the_persons_own_pins(member, author, robin):
    """`Pin.profile` verweist mit `CASCADE` auf `Profile` (Task 7.1) — dieselbe
    Kaskade wie bei Beiträgen und Meldungen, hier über den echten Weg geprüft."""
    theirs = Post.objects.create(author=robin, title="Theirs", body="b")
    own_pin = Pin.objects.create(profile=author, post=theirs)

    member.post(DELETE_URL)

    assert not Pin.objects.filter(pk=own_pin.pk).exists()
    assert Post.objects.filter(pk=theirs.pk).exists()  # der Beitrag selbst bleibt


def test_deleting_the_account_removes_pins_others_made_on_their_posts(member, author, robin):
    """`Pin.post` verweist ebenfalls mit `CASCADE` auf `Post` — der Beitrag
    verschwindet mit dem Account (D-78), sein Pin also mit ihm."""
    mine = Post.objects.create(author=author, title="Mine", body="b")
    foreign_pin = Pin.objects.create(profile=robin, post=mine)

    member.post(DELETE_URL)

    assert not Pin.objects.filter(pk=foreign_pin.pk).exists()
    assert Profile.objects.filter(nickname="robin").exists()


def test_a_pin_on_a_tombstoned_comment_disappears_from_the_pinboard(member, author, robin):
    """Anders als ein Beitrag verschwindet ein fremder Kommentar der gelöschten
    Person nicht (`Comment.author` ist `PROTECT`, Task 6.3) — er wird zur
    Hülle, die Zeile bleibt. Ihr Pin bleibt deshalb technisch bestehen, aber
    `apps.posts.listing.pinboard_page()` blendet ihn aus (FR-B23, Task 7.3)."""
    theirs = Post.objects.create(author=robin, title="Theirs", body="b")
    mine = create_comment(post=theirs, author=author, body="my comment")
    pin = Pin.objects.create(profile=robin, comment=mine)

    member.post(DELETE_URL)
    member.force_login(robin.user)

    mine.refresh_from_db()
    assert mine.is_tombstone
    assert Pin.objects.filter(pk=pin.pk).exists()  # die Zeile bleibt …
    html = member.get("/u/robin/").content.decode()
    assert '<article class="post-card">' not in html  # … aber wird nicht angezeigt


# Löschen des eigenen Kommentars (der View, FR-B16) --------------------------------------------


def test_the_author_of_a_comment_can_delete_it(member, robin):
    post = Post.objects.create(author=robin, title="Theirs", body="b")
    comment = create_comment(post=post, author=robin, body="oops")
    member.force_login(robin.user)

    response = member.post(f"/posts/{post.pk}/comments/{comment.pk}/delete/")

    assert response.status_code == 302
    comment.refresh_from_db()
    assert comment.is_tombstone


def test_someone_else_cannot_delete_a_comment(member, author, robin):
    post = Post.objects.create(author=author, title="Mine", body="b")
    comment = create_comment(post=post, author=robin, body="theirs")

    response = member.post(f"/posts/{post.pk}/comments/{comment.pk}/delete/")

    assert response.status_code == 302
    comment.refresh_from_db()
    assert not comment.is_tombstone
    assert comment.body == "theirs"


def test_a_comment_confirmation_page_is_shown_first(member, robin):
    post = Post.objects.create(author=robin, title="Theirs", body="b")
    comment = create_comment(post=post, author=robin, body="oops")
    member.force_login(robin.user)

    response = member.get(f"/posts/{post.pk}/comments/{comment.pk}/delete/")

    assert response.status_code == 200
    assert "#1" in response.content.decode()
    comment.refresh_from_db()
    assert not comment.is_tombstone


# Was Nutzende lesen ------------------------------------------------------------------------


def test_the_confirmation_page_names_posts_reports_and_comments(member):
    html = member.get(DELETE_URL).content.decode()

    assert "your posts" in html
    assert "the reports you sent" in html
    assert "disappear for everyone" in html
    assert "Comments you wrote under other people" in html


def test_the_confirmation_page_names_pins(member):
    html = member.get(DELETE_URL).content.decode()

    assert "Your own pins disappear" in html
    assert "other people's pins on your posts" in html


def test_the_confirmation_page_does_not_delete_anything(member, author):
    Post.objects.create(author=author, title="Mine", body="b")

    member.get(DELETE_URL)

    assert Post.objects.count() == 1
    assert User.objects.filter(pk=author.user.pk).exists()


def test_the_privacy_page_covers_posts_and_reports(gated_client):
    html = gated_client.get("/privacy/").content.decode()

    # welche Daten
    assert "Posts: the posts you write" in html
    assert "visible to everyone who is logged in, together with your nickname" in html
    assert "Reports: if you report someone" in html
    assert "Only the site owner can see it" in html
    # wie lange
    assert "Posts: until you delete them or your account." in html
    # wie löschbar
    assert "Edit or delete your own posts yourself" in html
    assert "Deleting a post also removes every comment and report about it." in html
    assert (
        "posts, pins, and the reports you sent, together with all reports about your posts" in html
    )


def test_the_privacy_page_covers_comments(gated_client):
    html = gated_client.get("/privacy/").content.decode()

    # welche Daten
    assert "Comments: the comments you write under posts" in html
    assert "a number that stays the same even if earlier comments are deleted" in html
    # wie lange
    assert "Comments: until you delete them." in html
    assert 'anonymous "deleted" entry' in html
    # wie löschbar
    assert "Delete your own comments yourself, any time, from the post they" in html


def test_the_privacy_page_covers_pins(gated_client):
    html = gated_client.get("/privacy/").content.decode()

    # welche Daten
    assert "Pins: which posts and comments you've pinned" in html
    assert "pinning something does not make it more visible to anyone else" in html
    # wie lange
    assert "Pins: until you unpin them or delete your account." in html
    # wie löschbar
    assert "Unpin your own pins yourself, any time" in html


def test_the_privacy_page_still_covers_everything_else(gated_client):
    html = gated_client.get("/privacy/").content.decode()

    for text in ("Argon2", "Test history", "STRATO", "14 days", "Delete your entire account"):
        assert text in html
