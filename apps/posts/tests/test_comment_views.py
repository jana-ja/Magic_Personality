"""
Tests für Kommentare auf der Beitragsseite (Task 6.2, FR-B13, FR-B15, FR-B18).

`test_comments.py` deckt Modell und Nummernvergabe ab; hier geht es um View,
Formular und Template: Reihenfolge, Antwort-Verweis, Anker, Grenze, Gast,
unsichtbarer Beitrag und Escaping.
"""

import re
from html.parser import HTMLParser

import pytest
from django.conf import settings
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.utils import timezone

from apps.posts.comments import create_comment
from apps.posts.models import COMMENT_MAX_LENGTH, Comment, Post, PostQuerySet

pytestmark = pytest.mark.django_db

HTMX = {"HTTP_HX_REQUEST": "true"}


@pytest.fixture
def member(gated_client, author):
    gated_client.force_login(author.user)
    return gated_client


@pytest.fixture
def post(author):
    return Post.objects.create(author=author, title="Original", body="Original text")


def comment_url(post):
    return f"/posts/{post.pk}/comment/"


def detail_url(post):
    return f"/posts/{post.pk}/"


def _comment_ids(html):
    return re.findall(r'id="c-(\d+)"', html)


def _comment_block(html, number):
    match = re.search(rf'<article id="c-{number}".*?</article>', html, re.S)
    return match.group(0) if match else ""


def _seed_comments(profile, post, count):
    for number in range(count):
        create_comment(post=post, author=profile, body=f"seed {number}")


def _query_count(client, url):
    with CaptureQueriesContext(connection) as queries:
        client.get(url)
    return len(queries)


# Reihenfolge und Zähler ------------------------------


def test_comments_render_oldest_first(member, post, author):
    create_comment(post=post, author=author, body="one")
    create_comment(post=post, author=author, body="two")
    create_comment(post=post, author=author, body="three")

    html = member.get(detail_url(post)).content.decode()

    assert _comment_ids(html) == ["1", "2", "3"]


def test_the_heading_counts_comments_and_uses_the_right_plural(member, post, author):
    assert "0 comments" in member.get(detail_url(post)).content.decode()

    create_comment(post=post, author=author, body="one")
    assert "1 comment" in member.get(detail_url(post)).content.decode()

    create_comment(post=post, author=author, body="two")
    assert "2 comments" in member.get(detail_url(post)).content.decode()


def test_each_comment_shows_its_own_authors_card(member, post, make_profile):
    robin = make_profile("robin")
    create_comment(post=post, author=robin, body="hi")

    html = member.get(detail_url(post)).content.decode()

    assert 'href="/u/robin/"' in html
    assert 'class="author-card author-card--small"' in html


# Antwort-Verweis und Anker (FR-B14, FR-B15) ------------------------------


def test_a_reply_shows_an_arrow_linking_to_its_anchor(member, post, author):
    first = create_comment(post=post, author=author, body="one")
    create_comment(post=post, author=author, body="re: one", reply_to=first)

    html = member.get(detail_url(post)).content.decode()

    assert '<a class="comment__reply-ref" href="#c-1">↪ #1</a>' in html


def test_a_top_level_comment_has_no_reference_arrow(member, post, author):
    create_comment(post=post, author=author, body="one")

    html = member.get(detail_url(post)).content.decode()

    assert "↪" not in html


def test_each_comment_has_its_own_numbered_anchor(member, post, author):
    create_comment(post=post, author=author, body="one")
    create_comment(post=post, author=author, body="two")

    html = member.get(detail_url(post)).content.decode()

    assert 'id="c-1"' in html
    assert 'id="c-2"' in html


def test_a_successful_submission_redirects_to_the_new_comments_anchor(member, post):
    response = member.post(comment_url(post), {"body": "hello"})

    assert response.status_code == 302
    assert response.url == f"/posts/{post.pk}/#c-1"


# „Reply" (FR-B15) ------------------------------


def test_the_reply_link_carries_the_comments_number(member, post, author):
    create_comment(post=post, author=author, body="one")

    html = member.get(detail_url(post)).content.decode()

    assert 'href="?reply=1#comment-form"' in html


def test_replying_via_the_query_param_prefills_the_form_and_shows_a_banner(member, post, author):
    create_comment(post=post, author=author, body="one")

    html = member.get(detail_url(post) + "?reply=1").content.decode()

    assert 'name="reply_to" value="1"' in html
    assert "Replying to #1" in html
    assert f'href="/posts/{post.pk}/#comment-form">Cancel</a>' in html


def test_an_unknown_reply_number_is_silently_ignored(member, post):
    html = member.get(detail_url(post) + "?reply=999").content.decode()

    assert "Replying to" not in html
    assert 'value="999"' not in html


def test_replying_through_the_form_links_the_new_comment(member, post, author):
    first = create_comment(post=post, author=author, body="one")

    member.post(comment_url(post), {"body": "re: one", "reply_to": first.number})

    reply = Comment.objects.get(number=2)
    assert reply.reply_to == first


def test_after_a_successful_htmx_reply_the_banner_is_gone(member, post, author):
    first = create_comment(post=post, author=author, body="one")

    html = member.post(
        comment_url(post), {"body": "re: one", "reply_to": first.number}, **HTMX
    ).content.decode()

    assert "Replying to" not in html
    assert "re: one</textarea>" not in html  # das Formular ist wieder leer


# Hüllen (D-79, vorgezogen aus Task 6.3 — hier direkt nachgestellt) ------------------------------


def _make_tombstone(post, author):
    comment = create_comment(post=post, author=author, body="soon gone")
    comment.deleted_at = timezone.now()
    comment.author = None
    comment.body = ""
    comment.save(update_fields=["deleted_at", "author", "body"])
    return comment


def test_a_tombstone_without_replies_is_hidden(member, post, author):
    _make_tombstone(post, author)

    html = member.get(detail_url(post)).content.decode()

    assert 'id="c-1"' not in html
    assert "0 comments" in html


def test_a_tombstone_with_a_reply_shows_only_its_number(member, post, author):
    # Erst antworten, dann löschen: create_comment() lehnt eine Antwort auf
    # eine bereits gelöschte Hülle ab (FR-B15) — die Reihenfolge hier bildet
    # nach, wie es in Wirklichkeit passiert (Task 6.3).
    original = create_comment(post=post, author=author, body="soon gone")
    create_comment(post=post, author=author, body="a reply", reply_to=original)
    original.deleted_at = timezone.now()
    original.author = None
    original.body = ""
    original.save(update_fields=["deleted_at", "author", "body"])

    html = member.get(detail_url(post)).content.decode()
    block = _comment_block(html, original.number)

    assert block != ""
    assert "deleted" in block
    assert "Reply" not in block
    assert "author-card" not in block


# Nur eingeloggt (FR-B8) ------------------------------


def test_a_guest_is_sent_to_the_login_and_nothing_is_created(gated_client, post):
    response = gated_client.post(comment_url(post), {"body": "hi"})

    assert response.status_code == 302
    assert response.url.startswith("/accounts/login/")
    assert Comment.objects.count() == 0


# Unsichtbarer Beitrag (FR-B9) ------------------------------


def test_an_invisible_post_refuses_the_comment(member, post, monkeypatch):
    monkeypatch.setattr(PostQuerySet, "visible_to", lambda self, profile: self.none())

    response = member.post(comment_url(post), {"body": "hi"})

    assert response.status_code == 404
    assert Comment.objects.count() == 0


def test_an_unknown_post_is_404(member):
    assert member.post("/posts/999999/comment/", {"body": "hi"}).status_code == 404


# Wer darf kommentieren ------------------------------


def test_anyone_who_can_see_the_post_can_comment_not_only_the_author(member, post, make_profile):
    stranger = make_profile("robin")
    member.force_login(stranger.user)

    response = member.post(comment_url(post), {"body": "hi"})

    assert response.status_code == 302
    assert Comment.objects.get().author == stranger


def test_the_author_cannot_be_chosen_by_the_client(member, post, author, make_profile):
    other = make_profile("robin")

    member.post(comment_url(post), {"body": "hi", "author": other.pk})

    assert Comment.objects.get().author == author


# Eingabe ------------------------------


def test_an_empty_comment_is_rejected(member, post):
    response = member.post(comment_url(post), {"body": "   "})

    assert response.status_code == 200
    assert Comment.objects.count() == 0


def test_a_comment_at_the_limit_is_accepted_and_beyond_is_rejected(member, post):
    member.post(comment_url(post), {"body": "x" * COMMENT_MAX_LENGTH})
    assert Comment.objects.count() == 1

    response = member.post(comment_url(post), {"body": "x" * (COMMENT_MAX_LENGTH + 1)})
    assert response.status_code == 200
    assert Comment.objects.count() == 1


def test_windows_line_endings_are_normalised(member, post):
    member.post(comment_url(post), {"body": "line one\r\nline two"})

    assert Comment.objects.get().body == "line one\nline two"


# Grenze (FR-B18) ------------------------------


def test_beyond_the_limit_no_comment_is_created_and_the_reason_is_shown(member, post, author):
    _seed_comments(author, post, settings.COMMENT_RATE_LIMIT_MAX_COMMENTS)

    response = member.post(comment_url(post), {"body": "one too many"})

    assert response.status_code == 429
    assert "commenting too fast" in response.content.decode()
    assert "one too many" in response.content.decode()
    assert Comment.objects.filter(author=author).count() == settings.COMMENT_RATE_LIMIT_MAX_COMMENTS


def test_the_limit_message_is_visible_with_htmx_too(member, post, author):
    _seed_comments(author, post, settings.COMMENT_RATE_LIMIT_MAX_COMMENTS)

    response = member.post(comment_url(post), {"body": "x"}, **HTMX)

    assert response.status_code == 200
    assert "commenting too fast" in response.content.decode()


def test_old_comments_do_not_count(member, post, author):
    _seed_comments(author, post, settings.COMMENT_RATE_LIMIT_MAX_COMMENTS)
    window = settings.COMMENT_RATE_LIMIT_WINDOW_SECONDS
    old = timezone.now() - timezone.timedelta(seconds=window + 60)
    Comment.objects.filter(author=author).update(created_at=old)

    assert member.post(comment_url(post), {"body": "fresh"}).status_code == 302


def test_other_peoples_comments_do_not_count(member, post, author, make_profile):
    _seed_comments(make_profile("robin"), post, settings.COMMENT_RATE_LIMIT_MAX_COMMENTS)

    assert member.post(comment_url(post), {"body": "fresh"}).status_code == 302


# HTMX ------------------------------


def test_a_successful_htmx_submission_returns_only_the_comments_fragment(member, post):
    response = member.post(comment_url(post), {"body": "hello"}, **HTMX)

    html = response.content.decode()
    assert response.status_code == 200
    assert "<html" not in html
    assert 'id="c-1"' in html
    assert "hello" in html
    assert Comment.objects.count() == 1


# Escaping / Injektionstest (wie Task 5.2, gegen Kommentare) ------------------------------


ALLOWED_TAGS = {"p", "br", "a"}
ALLOWED_ATTRIBUTES = {"a": {"href": r"https?://[^\s\"']*", "rel": "nofollow"}}


class _Validator(HTMLParser):
    """Wirft `AssertionError` bei jedem Tag oder Attribut außerhalb der Positivliste
    (wie `test_markdown.py`s Validator, hier für den viel kleineren erlaubten
    Umfang von `urlize`/`linebreaks`)."""

    def handle_starttag(self, tag, attrs):
        assert tag in ALLOWED_TAGS, f"unexpected tag <{tag}>"
        allowed = ALLOWED_ATTRIBUTES.get(tag, {})
        for name, value in attrs:
            assert name in allowed, f"unexpected attribute {name!r} on <{tag}>"
            assert re.fullmatch(allowed[name], value or ""), f"bad {name}={value!r} on <{tag}>"

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)

    def handle_comment(self, data):
        raise AssertionError("HTML comment in output")


def assert_only_allowed_markup(html):
    validator = _Validator()
    validator.feed(html)
    validator.close()


INJECTION_CORPUS = [
    "<script>alert(1)</script>",
    "<SCRIPT SRC=http://evil.example/x.js></SCRIPT>",
    "<img src=x onerror=alert(1)>",
    "<svg onload=alert(1)>",
    "<iframe src=javascript:alert(1)></iframe>",
    "<style>body{display:none}</style>",
    '<div onclick="alert(1)">click</div>',
    '<a href="javascript:alert(1)">x</a>',
    "<!-- comment --><b>x</b>",
    "javascript:alert(1)",
    "[click](javascript:alert(1))",
    "&lt;script&gt;alert(1)&lt;/script&gt;",
    'http://evil.example/"onmouseover=alert(1)',
    "<math><mi xlink:href=javascript:alert(1)>x</mi></math>",
    "line one\n<script>alert(1)</script>\nline two",
    '<a href="http://a.example" onmouseover="alert(1)">x</a>',
]


def _comment_body_html(html, number):
    """Nur das gerenderte Innere von `.comment__body` — der Rest der Seite
    (Nav, Überschriften, der „Reply"-Link mit seinem `?reply=`-Ziel) hat
    eigene, legitime Tags und Attribute, die mit der engen Positivliste
    hier gar nicht gemeint sind."""
    block = _comment_block(html, number)
    match = re.search(r'<div class="comment__body">(.*?)</div>', block, re.S)
    return match.group(1) if match else ""


@pytest.mark.parametrize("body", INJECTION_CORPUS)
def test_injection_corpus_never_becomes_markup(member, post, body):
    response = member.post(comment_url(post), {"body": body}, follow=True)

    rendered = _comment_body_html(response.content.decode(), 1)
    assert rendered != ""  # der Kommentar ist tatsächlich angelegt worden
    assert_only_allowed_markup(rendered)
    lowered = rendered.lower()
    for forbidden in ("<script", "<img", "<iframe", "<svg", "<style", "<math"):
        assert forbidden not in lowered
    assert 'href="javascript' not in lowered


@pytest.mark.parametrize("body", INJECTION_CORPUS)
def test_injection_corpus_is_harmless_via_htmx_too(member, post, body):
    response = member.post(comment_url(post), {"body": body}, **HTMX)

    rendered = _comment_body_html(response.content.decode(), 1)
    assert rendered != ""
    assert_only_allowed_markup(rendered)


def test_a_null_byte_is_rejected_before_it_ever_reaches_the_comment(member, post):
    """Nicht im Korpus oben (das prüft, was *gerendert* wird): Djangos
    `CharField` weist ein `\\x00` schon bei der Formularvalidierung ab, der
    Kommentar entsteht gar nicht erst — eine eigene Absicherung unterhalb
    von `urlize`/`linebreaks`."""
    response = member.post(comment_url(post), {"body": "\x00<script>alert(1)</script>"})

    assert response.status_code == 200
    assert "Null characters are not allowed" in response.content.decode()
    assert Comment.objects.count() == 0


def test_the_validator_itself_catches_dangerous_markup():
    """Schutz vor einem Test, der nichts prüft: die Positivliste schlägt an."""
    for bad in ("<script>alert(1)</script>", '<img src="x">', '<p onclick="1">x</p>'):
        with pytest.raises(AssertionError):
            assert_only_allowed_markup(bad)


# Abfragen ------------------------------


def test_more_comments_do_not_cost_more_queries(member, post, author, make_profile):
    create_comment(post=post, author=author, body="one")
    member.get(detail_url(post))  # legt die PostSeen-Zeile an (Task 6.6), vor der Messung
    one = _query_count(member, detail_url(post))

    last = None
    for name in ("robin", "sam", "kai", "lee"):
        last = create_comment(post=post, author=make_profile(name), body=name)
    create_comment(post=post, author=author, body="a reply", reply_to=last)
    many = _query_count(member, detail_url(post))

    assert many == one
