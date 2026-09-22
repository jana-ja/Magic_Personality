"""
Zugriffsmatrix aller Adressen der Beiträge (Task 5.9, FR-B4, FR-B8, FR-B10,
D-78) und ihrer Kommentare (Task 6.3, FR-B16).

Gleiche Idee wie `apps/social/tests/test_access_control.py`: jede Adresse wird
systematisch durchgegangen, und ein Test sorgt dafür, dass eine **neue** Adresse
nicht unbemerkt an der Matrix vorbeikommt.
"""

import pytest
from django.conf import settings
from django.test import Client

from apps.core import gate
from apps.posts import urls as posts_urls
from apps.posts.comments import create_comment
from apps.posts.models import Post, Report

pytestmark = pytest.mark.django_db

#: Alle Adressen der Posts-App und der Kombinationsliste (`colors:posts`).
NAMES = [
    "new",
    "detail",
    "edit",
    "delete",
    "report",
    "report_thanks",
    "comment",
    "comment_delete",
    "colors_posts",
]
#: Adressen, die nur die Autorin bzw. der Autor erreicht — bei "comment_delete"
#: die des Kommentars, hier (Fixtur `comment`) dieselbe Person wie beim Beitrag.
AUTHOR_ONLY = ["edit", "delete", "comment_delete"]
#: Adressen, die etwas speichern oder löschen (also CSRF-geschützt sein müssen).
WRITING = ["new", "edit", "delete", "report", "comment", "comment_delete"]
#: Adressen, die **nur** POST annehmen (kein GET, anders als die übrigen WRITING-Adressen).
POST_ONLY = ["comment"]


def _path(name, post, comment):
    return {
        "new": "/posts/new/",
        "detail": f"/posts/{post.pk}/",
        "edit": f"/posts/{post.pk}/edit/",
        "delete": f"/posts/{post.pk}/delete/",
        "report": f"/posts/{post.pk}/report/",
        "report_thanks": f"/posts/{post.pk}/report/thanks/",
        "comment": f"/posts/{post.pk}/comment/",
        "comment_delete": f"/posts/{post.pk}/comments/{comment.pk}/delete/",
        "colors_posts": "/colors/wg/posts/",
    }[name]


@pytest.fixture
def post(author):
    return Post.objects.create(author=author, title="Original", body="Original text", colors="WG")


@pytest.fixture
def comment(post, author):
    return create_comment(post=post, author=author, body="Original comment")


@pytest.fixture
def stranger(make_profile):
    return make_profile("robin")


def test_the_matrix_knows_every_address_of_the_posts_app():
    known = {pattern.name for pattern in posts_urls.urlpatterns} | {"colors_posts"}

    assert known == set(NAMES)


# Gate und Login ----------------------------------------------------------------------------


@pytest.mark.parametrize("name", NAMES)
def test_without_the_gate_cookie_every_address_is_locked(client, post, comment, name):
    path = _path(name, post, comment)
    for response in (client.get(path), client.post(path, {})):
        assert response.status_code == 302
        assert response.url.startswith("/gate/")


@pytest.mark.parametrize("name", NAMES)
def test_without_a_login_every_address_leads_to_the_login_and_changes_nothing(
    gated_client, post, comment, name
):
    path = _path(name, post, comment)
    for response in (
        gated_client.get(path),
        gated_client.post(path, {"title": "x", "body": "y", "reason": "z"}),
    ):
        assert response.status_code == 302
        assert response.url.startswith("/accounts/login/")

    assert Post.objects.get().title == "Original"
    assert Report.objects.count() == 0


# Autorenrechte ------------------------------------------------------------------------------


@pytest.mark.parametrize("name", AUTHOR_ONLY)
def test_someone_else_is_sent_to_the_post_and_nothing_changes(
    gated_client, post, comment, stranger, name
):
    gated_client.force_login(stranger.user)
    path = _path(name, post, comment)

    for response in (
        gated_client.get(path),
        gated_client.post(path, {"title": "Hijacked", "body": "Hijacked"}),
    ):
        assert response.status_code == 302
        assert response.url == f"/posts/{post.pk}/"

    post.refresh_from_db()
    assert (post.title, post.body, post.edited_at) == ("Original", "Original text", None)
    comment.refresh_from_db()
    assert not comment.is_tombstone


def test_comment_delete_checks_the_comments_author_not_the_posts(
    gated_client, post, author, stranger
):
    """Anders als `edit`/`delete`: hier entscheidet, wer den Kommentar geschrieben
    hat — nicht, wer den Beitrag geschrieben hat (FR-B16)."""
    foreign_comment = create_comment(post=post, author=stranger, body="not yours")
    gated_client.force_login(author.user)  # die Autorin/der Autor des Beitrags

    response = gated_client.post(_path("comment_delete", post, foreign_comment))

    assert response.status_code == 302
    assert response.url == f"/posts/{post.pk}/"
    foreign_comment.refresh_from_db()
    assert not foreign_comment.is_tombstone


def test_the_author_can_use_every_address_of_their_own_post(gated_client, post, comment, author):
    gated_client.force_login(author.user)

    for name in ("new", "detail", "edit", "delete", "comment_delete"):
        assert gated_client.get(_path(name, post, comment)).status_code == 200, name


def test_the_author_cannot_report_their_own_post(gated_client, post, comment, author):
    gated_client.force_login(author.user)

    assert gated_client.get(_path("report", post, comment)).status_code == 302
    assert gated_client.post(_path("report", post, comment), {}).status_code == 302
    assert Report.objects.count() == 0


# CSRF ----------------------------------------------------------------------------------------


@pytest.mark.parametrize("name", WRITING)
def test_every_writing_address_refuses_a_post_without_a_csrf_token(post, comment, author, name):
    """Der Test-Client prüft CSRF sonst nicht: hier mit eingeschalteter Prüfung, Gate-Cookie
    und Anmeldung, aber ohne Token."""
    strict = Client(enforce_csrf_checks=True)
    strict.cookies[settings.GATE_COOKIE_NAME] = gate.sign_gate_cookie()
    strict.force_login(author.user)
    other = Post.objects.create(author=author, title="Other", body="b")
    target = post if name != "report" else other

    response = strict.post(_path(name, target, comment), {"title": "x", "body": "y", "reason": "z"})

    assert response.status_code == 403
    assert Post.objects.count() == 2
    assert Post.objects.get(pk=post.pk).title == "Original"


# Methoden --------------------------------------------------------------------------------------


@pytest.mark.parametrize("name", ["detail", "report_thanks", "colors_posts"])
def test_read_only_addresses_refuse_writing_methods(gated_client, post, comment, stranger, name):
    gated_client.force_login(stranger.user)
    path = _path(name, post, comment)

    for method in ("post", "put", "patch", "delete"):
        assert getattr(gated_client, method)(path).status_code == 405


@pytest.mark.parametrize("name", POST_ONLY)
def test_post_only_addresses_refuse_get_and_other_methods(
    gated_client, post, comment, stranger, name
):
    gated_client.force_login(stranger.user)
    path = _path(name, post, comment)

    for method in ("get", "put", "patch", "delete"):
        assert getattr(gated_client, method)(path).status_code == 405
