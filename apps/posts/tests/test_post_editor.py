"""
Tests für Beitrag schreiben, bearbeiten, löschen (Task 5.3, FR-B1 bis FR-B4,
FR-B8, FR-B11, D-78).
"""

import pytest
from django.conf import settings
from django.utils import timezone

from apps.posts.models import BODY_MAX_LENGTH, TITLE_MAX_LENGTH, Post

pytestmark = pytest.mark.django_db

NEW_URL = "/posts/new/"
HTMX = {"HTTP_HX_REQUEST": "true"}


@pytest.fixture
def member(gated_client, author):
    """Ein Test-Client mit Gate-Cookie, angemeldet als `author`."""
    gated_client.force_login(author.user)
    return gated_client


@pytest.fixture
def post(author):
    return Post.objects.create(author=author, title="Original", body="Original text", colors="WG")


def _urls(post):
    return {
        "detail": f"/posts/{post.pk}/",
        "edit": f"/posts/{post.pk}/edit/",
        "delete": f"/posts/{post.pk}/delete/",
    }


# Zugriff --------------------------------------------------------------------------


@pytest.mark.parametrize("name", ["new", "detail", "edit", "delete"])
def test_without_the_gate_cookie_everything_redirects_to_the_gate(member, post, name):
    member.cookies.clear()
    url = NEW_URL if name == "new" else _urls(post)[name]

    response = member.get(url)

    assert response.status_code == 302
    assert response.url.startswith("/gate/")


@pytest.mark.parametrize("name", ["new", "detail", "edit", "delete"])
def test_guests_are_sent_to_the_login(gated_client, post, name):
    url = NEW_URL if name == "new" else _urls(post)[name]

    for response in (gated_client.get(url), gated_client.post(url, {"title": "x", "body": "y"})):
        assert response.status_code == 302
        assert response.url.startswith("/accounts/login/")
    assert Post.objects.count() == 1


def test_an_account_without_a_profile_gets_404_not_a_server_error(gated_client, db):
    from apps.accounts.models import User

    user = User.objects.create_user(email="noprofile@example.com", password="a-long-enough-pw")
    gated_client.force_login(user)

    assert gated_client.get(NEW_URL).status_code == 404


# Neu --------------------------------------------------------------------------------


def test_the_editor_form_is_shown(member):
    response = member.get(NEW_URL)

    html = response.content.decode()
    assert response.status_code == 200
    assert 'name="title"' in html
    assert 'name="body"' in html
    assert 'name="colors"' in html
    assert "Markdown" in html


def test_colors_can_be_prefilled_from_the_url(member):
    response = member.get(NEW_URL + "?colors=gw")

    assert response.context["form"].initial["colors"] == ["G", "W"]
    assert response.content.decode().count('aria-checked="true"') == 2


def test_invalid_prefill_is_ignored(member):
    html = member.get(NEW_URL + "?colors=xx").content.decode()

    assert 'aria-checked="true"' not in html


def test_a_post_can_be_written_without_colors(member, author):
    response = member.post(NEW_URL, {"title": "General thoughts", "body": "Some **text**."})

    post = Post.objects.get()
    assert response.status_code == 302
    assert response.url == f"/posts/{post.pk}/"
    assert post.author == author
    assert post.title == "General thoughts"
    assert post.body == "Some **text**."
    assert post.colors == ""
    assert post.edited_at is None


def test_colors_are_stored_canonically_whatever_the_order(member):
    member.post(NEW_URL, {"title": "t", "body": "b", "colors": ["G", "W"]})

    assert Post.objects.get().colors == "WG"


def test_the_author_cannot_be_chosen_by_the_client(member, author, make_profile):
    other = make_profile("robin")

    member.post(NEW_URL, {"title": "t", "body": "b", "author": other.pk, "author_id": other.pk})

    assert Post.objects.get().author == author


def test_windows_line_endings_are_stored_as_line_feeds(member):
    member.post(NEW_URL, {"title": "t", "body": "line one\r\n\r\nline two\r\n"})

    assert Post.objects.get().body == "line one\n\nline two"


def test_leading_indentation_of_code_is_kept(member):
    member.post(NEW_URL, {"title": "t", "body": "    indented code\n\ntext"})

    assert Post.objects.get().body.startswith("    indented code")


@pytest.mark.parametrize(
    ("data", "field"),
    [
        ({"title": "", "body": "b"}, "title"),
        ({"title": "   ", "body": "b"}, "title"),
        ({"title": "t", "body": ""}, "body"),
        ({"title": "t", "body": "  \n \n "}, "body"),
        ({"title": "x" * (TITLE_MAX_LENGTH + 1), "body": "b"}, "title"),
        ({"title": "t", "body": "x" * (BODY_MAX_LENGTH + 1)}, "body"),
        ({"title": "t", "body": "b", "colors": ["X"]}, "colors"),
        ({"title": "t", "body": "b", "colors": ["w", "g"]}, "colors"),
    ],
)
def test_invalid_input_is_rejected_and_shown_again(member, data, field):
    response = member.post(NEW_URL, data)

    assert response.status_code == 200
    assert response.context["form"].errors.keys() == {field}
    assert Post.objects.count() == 0


def test_a_rejected_form_keeps_what_was_typed(member):
    response = member.post(NEW_URL, {"title": "", "body": "My long text", "colors": ["U"]})

    html = response.content.decode()
    assert "My long text" in html
    assert 'aria-checked="true"' in html


def test_limits_are_checked_after_normalising_line_endings(member):
    """10 000 Zeichen mit CRLF sind nach dem Normalisieren weniger als 10 000."""
    lines = "ab\r\n" * 2400  # 4 Zeichen roh, 3 nach der Normalisierung

    member.post(NEW_URL, {"title": "t", "body": lines})

    assert Post.objects.count() == 1


def test_the_text_is_escaped_when_shown_again(member):
    response = member.post(NEW_URL, {"title": "", "body": "<script>alert(1)</script>"})

    html = response.content.decode()
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in html


# Grenze (FR-B11) -----------------------------------------------------------------


def _fill_up_the_limit(author):
    for number in range(settings.POST_RATE_LIMIT_MAX_POSTS):
        Post.objects.create(author=author, title=f"Post {number}", body="b")


def test_beyond_the_limit_no_post_is_created_and_the_reason_is_shown(member, author):
    _fill_up_the_limit(author)

    response = member.post(NEW_URL, {"title": "One too many", "body": "b"})

    assert response.status_code == 429
    assert "posting too fast" in response.content.decode()
    assert "One too many" in response.content.decode()  # der Text geht nicht verloren
    assert Post.objects.count() == settings.POST_RATE_LIMIT_MAX_POSTS


def test_posts_older_than_the_window_do_not_count(member, author):
    _fill_up_the_limit(author)
    old = timezone.now() - timezone.timedelta(seconds=settings.POST_RATE_LIMIT_WINDOW_SECONDS + 60)
    Post.objects.update(created_at=old)

    assert member.post(NEW_URL, {"title": "Fine", "body": "b"}).status_code == 302


def test_other_peoples_posts_do_not_count(member, make_profile):
    _fill_up_the_limit(make_profile("robin"))

    assert member.post(NEW_URL, {"title": "Fine", "body": "b"}).status_code == 302


def test_the_limit_does_not_block_editing(member, author, post):
    _fill_up_the_limit(author)

    response = member.post(_urls(post)["edit"], {"title": "Changed", "body": "Original text"})

    assert response.status_code == 302
    post.refresh_from_db()
    assert post.title == "Changed"


# Vorschau ------------------------------------------------------------------------------


def test_the_preview_renders_markdown_and_saves_nothing(member):
    response = member.post(
        NEW_URL, {"action": "preview", "title": "T", "body": "**bold** text", "colors": ["W"]}
    )

    html = response.content.decode()
    assert response.status_code == 200
    assert "<strong>bold</strong>" in html
    assert 'name="body"' in html  # das ganze Formular, ohne JavaScript nutzbar
    assert "**bold** text" in html  # der Quelltext bleibt im Feld erhalten
    assert Post.objects.count() == 0


def test_the_preview_works_with_an_unfinished_form(member):
    response = member.post(NEW_URL, {"action": "preview", "title": "", "body": ""})

    assert response.status_code == 200
    assert "Nothing to preview yet." in response.content.decode()
    assert "This field is required" not in response.content.decode()


def test_the_htmx_preview_returns_only_the_fragment(member):
    response = member.post(NEW_URL, {"action": "preview", "body": "*hi*"}, **HTMX)

    html = response.content.decode()
    assert "<html" not in html
    assert "<em>hi</em>" in html
    assert Post.objects.count() == 0


def test_the_preview_is_safe_and_does_not_use_up_the_limit(member, author):
    _fill_up_the_limit(author)

    response = member.post(NEW_URL, {"action": "preview", "body": "<script>alert(1)</script>"})

    assert response.status_code == 200
    assert "<script>alert(1)</script>" not in response.content.decode()


def test_the_preview_of_an_edit_does_not_change_the_post(member, post):
    member.post(_urls(post)["edit"], {"action": "preview", "title": "New", "body": "New body"})

    post.refresh_from_db()
    assert (post.title, post.body, post.edited_at) == ("Original", "Original text", None)


# Bearbeiten ------------------------------------------------------------------------------


def test_the_edit_form_starts_with_the_current_values(member, post):
    html = member.get(_urls(post)["edit"]).content.decode()

    assert 'value="Original"' in html
    assert "Original text" in html
    assert html.count('aria-checked="true"') == 2  # W und G


def test_an_edit_saves_only_what_changed_and_marks_it_edited(member, post):
    before = post.created_at

    response = member.post(
        _urls(post)["edit"],
        {"title": "Changed", "body": "Original text", "colors": ["G", "W"]},
    )

    post.refresh_from_db()
    assert response.status_code == 302
    assert post.title == "Changed"
    assert post.body == "Original text"
    assert post.colors == "WG"
    assert post.edited_at is not None
    assert post.created_at == before


def test_an_unchanged_form_leaves_edited_at_alone(member, post):
    member.post(
        _urls(post)["edit"],
        {"title": "Original", "body": "Original text\r\n", "colors": ["G", "W"]},
    )

    post.refresh_from_db()
    assert post.edited_at is None


def test_colors_can_be_changed_and_removed(member, post):
    same = {"title": "Original", "body": "Original text"}

    member.post(_urls(post)["edit"], {**same, "colors": ["U"]})
    post.refresh_from_db()
    assert post.colors == "U"

    member.post(_urls(post)["edit"], same)
    post.refresh_from_db()
    assert post.colors == ""
    assert post.edited_at is not None


def test_an_invalid_edit_changes_nothing(member, post):
    response = member.post(_urls(post)["edit"], {"title": "", "body": "x"})

    post.refresh_from_db()
    assert response.status_code == 200
    assert (post.title, post.body, post.edited_at) == ("Original", "Original text", None)


def test_someone_else_cannot_edit_and_is_sent_to_the_post(member, make_profile, post):
    other = make_profile("robin")
    member.force_login(other.user)

    got = member.get(_urls(post)["edit"])
    posted = member.post(_urls(post)["edit"], {"title": "Hijacked", "body": "Hijacked"})

    for response in (got, posted):
        assert response.status_code == 302
        assert response.url == _urls(post)["detail"]
    post.refresh_from_db()
    assert (post.title, post.body) == ("Original", "Original text")


def test_editing_an_unknown_post_is_404(member):
    assert member.get("/posts/999999/edit/").status_code == 404


# Löschen ----------------------------------------------------------------------------------


def test_get_only_asks_for_confirmation(member, post):
    response = member.get(_urls(post)["delete"])

    assert response.status_code == 200
    assert "Original" in response.content.decode()
    assert Post.objects.filter(pk=post.pk).exists()


def test_post_deletes_and_leaves_for_the_profile(member, author, post):
    response = member.post(_urls(post)["delete"])

    assert response.status_code == 302
    assert response.url == author.get_absolute_url()
    assert not Post.objects.filter(pk=post.pk).exists()


def test_someone_else_cannot_delete(member, make_profile, post):
    member.force_login(make_profile("robin").user)

    got = member.get(_urls(post)["delete"])
    posted = member.post(_urls(post)["delete"])

    for response in (got, posted):
        assert response.status_code == 302
        assert response.url == _urls(post)["detail"]
    assert Post.objects.filter(pk=post.pk).exists()


def test_deleting_an_unknown_post_is_404(member):
    assert member.post("/posts/999999/delete/").status_code == 404


def test_only_get_and_post_are_allowed(member, post):
    for name in ("edit", "delete"):
        assert member.put(_urls(post)[name]).status_code == 405
        assert member.delete(_urls(post)[name]).status_code == 405
    assert member.put(NEW_URL).status_code == 405


# Beitragsseite (vorläufig, Task 5.4 baut sie aus) ------------------------------------------


def test_the_detail_page_shows_title_author_and_rendered_text(member, author):
    post = Post.objects.create(author=author, title="A title", body="**bold** and <b>x</b>")

    html = member.get(_urls(post)["detail"]).content.decode()

    assert "A title" in html
    assert "alex" in html
    assert "<strong>bold</strong>" in html
    assert "<b>x</b>" not in html


def test_edit_and_delete_are_offered_to_the_author_only(member, make_profile, post):
    author_html = member.get(_urls(post)["detail"]).content.decode()
    member.force_login(make_profile("robin").user)
    other_html = member.get(_urls(post)["detail"]).content.decode()

    assert _urls(post)["edit"] in author_html
    assert _urls(post)["delete"] in author_html
    assert _urls(post)["edit"] not in other_html
    assert _urls(post)["delete"] not in other_html


def test_an_unknown_post_is_404(member):
    assert member.get("/posts/999999/").status_code == 404


# Sichtbarkeit: alles läuft durch visible_to ---------------------------------------------


@pytest.mark.parametrize("name", ["detail", "edit", "delete"])
def test_every_read_goes_through_visible_to(member, post, monkeypatch, name):
    """Ersetzt man die Prüfung durch eine, die nichts durchlässt, sieht kein
    Pfad den Beitrag mehr — auch nicht die Autorin (Vorstufe von Task 7.4)."""
    from apps.posts.models import PostQuerySet

    monkeypatch.setattr(PostQuerySet, "visible_to", lambda self, profile: self.none())

    assert member.get(_urls(post)[name]).status_code == 404
