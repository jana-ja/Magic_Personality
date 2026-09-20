"""
Tests für Account-Löschung und Datenschutz mit Beiträgen (Task 5.8, FR-B12, D-78, D-81).

Die Kaskade selbst (Beitrag und Meldung verschwinden mit Profil bzw. Beitrag)
steht schon in test_models.py und test_reports.py; hier geht es um den echten
Weg über die View und um das, was Nutzende darüber lesen.
"""

import pytest
from django.db import models

from apps.accounts.models import Profile, User
from apps.posts.models import Post, Report

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
    """Beiträge und Meldungen gehören der Person: jeder Verweis der Posts-App auf
    ein Profil kaskadiert. Kommt mit v1.4 eine Ausnahme dazu (Kommentare werden
    zu Hüllen, D-79), gehört sie bewusst hier begründet hinein."""
    for model in (Post, Report):
        for field in model._meta.fields:
            if field.is_relation and field.related_model is Profile:
                assert field.remote_field.on_delete is models.CASCADE, (model, field.name)


# Was Nutzende lesen ------------------------------------------------------------------------


def test_the_confirmation_page_names_posts_and_reports(member):
    html = member.get(DELETE_URL).content.decode()

    assert "your posts" in html
    assert "the reports you sent" in html
    assert "disappear for everyone" in html


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
    assert "Deleting a post also removes every report about it." in html
    assert "posts, and the reports you sent, together with all reports about your posts" in html


def test_the_privacy_page_still_covers_everything_else(gated_client):
    html = gated_client.get("/privacy/").content.decode()

    for text in ("Argon2", "Test history", "STRATO", "14 days", "Delete your entire account"):
        assert text in html
