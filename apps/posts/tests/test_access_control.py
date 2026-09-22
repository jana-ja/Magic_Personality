"""
Zugriffsmatrix aller Adressen der Beiträge (Task 5.9, FR-B4, FR-B8, FR-B10, D-78).

Gleiche Idee wie `apps/social/tests/test_access_control.py`: jede Adresse wird
systematisch durchgegangen, und ein Test sorgt dafür, dass eine **neue** Adresse
nicht unbemerkt an der Matrix vorbeikommt.
"""

import pytest
from django.conf import settings
from django.test import Client

from apps.core import gate
from apps.posts import urls as posts_urls
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
    "colors_posts",
]
#: Adressen, die nur die Autorin bzw. der Autor erreicht.
AUTHOR_ONLY = ["edit", "delete"]
#: Adressen, die etwas speichern oder löschen (also CSRF-geschützt sein müssen).
WRITING = ["new", "edit", "delete", "report", "comment"]
#: Adressen, die **nur** POST annehmen (kein GET, anders als die übrigen WRITING-Adressen).
POST_ONLY = ["comment"]


def _path(name, post):
    return {
        "new": "/posts/new/",
        "detail": f"/posts/{post.pk}/",
        "edit": f"/posts/{post.pk}/edit/",
        "delete": f"/posts/{post.pk}/delete/",
        "report": f"/posts/{post.pk}/report/",
        "report_thanks": f"/posts/{post.pk}/report/thanks/",
        "comment": f"/posts/{post.pk}/comment/",
        "colors_posts": "/colors/wg/posts/",
    }[name]


@pytest.fixture
def post(author):
    return Post.objects.create(author=author, title="Original", body="Original text", colors="WG")


@pytest.fixture
def stranger(make_profile):
    return make_profile("robin")


def test_the_matrix_knows_every_address_of_the_posts_app():
    known = {pattern.name for pattern in posts_urls.urlpatterns} | {"colors_posts"}

    assert known == set(NAMES)


# Gate und Login ----------------------------------------------------------------------------


@pytest.mark.parametrize("name", NAMES)
def test_without_the_gate_cookie_every_address_is_locked(client, post, name):
    for response in (client.get(_path(name, post)), client.post(_path(name, post), {})):
        assert response.status_code == 302
        assert response.url.startswith("/gate/")


@pytest.mark.parametrize("name", NAMES)
def test_without_a_login_every_address_leads_to_the_login_and_changes_nothing(
    gated_client, post, name
):
    for response in (
        gated_client.get(_path(name, post)),
        gated_client.post(_path(name, post), {"title": "x", "body": "y", "reason": "z"}),
    ):
        assert response.status_code == 302
        assert response.url.startswith("/accounts/login/")

    assert Post.objects.get().title == "Original"
    assert Report.objects.count() == 0


# Autorenrechte ------------------------------------------------------------------------------


@pytest.mark.parametrize("name", AUTHOR_ONLY)
def test_someone_else_is_sent_to_the_post_and_nothing_changes(gated_client, post, stranger, name):
    gated_client.force_login(stranger.user)

    for response in (
        gated_client.get(_path(name, post)),
        gated_client.post(_path(name, post), {"title": "Hijacked", "body": "Hijacked"}),
    ):
        assert response.status_code == 302
        assert response.url == f"/posts/{post.pk}/"

    post.refresh_from_db()
    assert (post.title, post.body, post.edited_at) == ("Original", "Original text", None)


def test_the_author_can_use_every_address_of_their_own_post(gated_client, post, author):
    gated_client.force_login(author.user)

    for name in ("new", "detail", "edit", "delete"):
        assert gated_client.get(_path(name, post)).status_code == 200, name


def test_the_author_cannot_report_their_own_post(gated_client, post, author):
    gated_client.force_login(author.user)

    assert gated_client.get(_path("report", post)).status_code == 302
    assert gated_client.post(_path("report", post), {}).status_code == 302
    assert Report.objects.count() == 0


# CSRF ----------------------------------------------------------------------------------------


@pytest.mark.parametrize("name", WRITING)
def test_every_writing_address_refuses_a_post_without_a_csrf_token(post, author, name):
    """Der Test-Client prüft CSRF sonst nicht: hier mit eingeschalteter Prüfung, Gate-Cookie
    und Anmeldung, aber ohne Token."""
    strict = Client(enforce_csrf_checks=True)
    strict.cookies[settings.GATE_COOKIE_NAME] = gate.sign_gate_cookie()
    strict.force_login(author.user)
    other = Post.objects.create(author=author, title="Other", body="b")
    target = post if name != "report" else other

    response = strict.post(_path(name, target), {"title": "x", "body": "y", "reason": "z"})

    assert response.status_code == 403
    assert Post.objects.count() == 2
    assert Post.objects.get(pk=post.pk).title == "Original"


# Methoden --------------------------------------------------------------------------------------


@pytest.mark.parametrize("name", ["detail", "report_thanks", "colors_posts"])
def test_read_only_addresses_refuse_writing_methods(gated_client, post, stranger, name):
    gated_client.force_login(stranger.user)

    for method in ("post", "put", "patch", "delete"):
        assert getattr(gated_client, method)(_path(name, post)).status_code == 405


@pytest.mark.parametrize("name", POST_ONLY)
def test_post_only_addresses_refuse_get_and_other_methods(gated_client, post, stranger, name):
    gated_client.force_login(stranger.user)

    for method in ("get", "put", "patch", "delete"):
        assert getattr(gated_client, method)(_path(name, post)).status_code == 405
