"""
Tests für den Profil-Tab „Comments" (Task 6.4, FR-B17, FR-B8, FR-B9, D-79).
"""

import re

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.utils import timezone

from apps.posts.comments import create_comment
from apps.posts.listing import PAGE_SIZE
from apps.posts.models import Comment, Post, PostQuerySet

pytestmark = pytest.mark.django_db

URL = "/u/alex/comments/"


@pytest.fixture
def member(gated_client, author):
    gated_client.force_login(author.user)
    return gated_client


@pytest.fixture
def post(author):
    return Post.objects.create(author=author, title="The Post", body="b")


def _cards(html):
    return re.findall(r'<article class="post-card">.*?</article>', html, re.S)


def _numbers(html):
    return re.findall(r'<span class="comment__number">#(\d+)</span>', html)


def _tabs(html):
    return re.search(r'<nav class="profile-tabs".*?</nav>', html, re.S).group(0)


def _write(post, author, count, start=0):
    """`count` Kommentare mit aufsteigender Zeit; die Nummern selbst kommen aus
    dem Beitrags-Zähler und sind deshalb unabhängig vom `created_at`-Zeitstempel."""
    base = timezone.now() - timezone.timedelta(days=count + start)
    comments = []
    for number in range(start, start + count):
        comment = create_comment(post=post, author=author, body=f"Comment {number}")
        when = base + timezone.timedelta(days=number - start)
        Comment.objects.filter(pk=comment.pk).update(created_at=when)
        comments.append(comment)
    return comments


# Zugriff ------------------------------------------------------------------------------


def test_the_tab_needs_the_gate_cookie(client):
    response = client.get(URL)

    assert response.status_code == 302
    assert response.url.startswith("/gate/")


def test_the_tab_needs_a_login(gated_client):
    response = gated_client.get(URL)

    assert response.status_code == 302
    assert response.url.startswith("/accounts/login/")


def test_an_unknown_nickname_is_404(member):
    assert member.get("/u/nobody/comments/").status_code == 404


# Tab-Leiste -----------------------------------------------------------------------------


def test_the_tab_sits_between_posts_and_friends(member):
    tabs = _tabs(member.get(URL).content.decode())

    assert tabs.index("Posts") < tabs.index("Comments") < tabs.index("Friends")


def test_the_comments_tab_is_the_current_page_on_its_own_address(member):
    tabs = _tabs(member.get(URL).content.decode())

    assert '<a href="/u/alex/comments/" aria-current="page">Comments</a>' in tabs
    assert tabs.count("aria-current") == 1


# Liste ---------------------------------------------------------------------------------


def test_comments_are_shown_newest_first(member, post, author):
    _write(post, author, 3)

    html = member.get(URL).content.decode()

    assert [f"Comment {n}" for n in (2, 1, 0)] == re.findall(
        r'class="post-card__excerpt">([^<]*)</p>', html
    )


def test_someone_elses_profile_lists_that_persons_comments(member, make_profile):
    robin = make_profile("robin")
    post = Post.objects.create(author=robin, title="Robin's post", body="b")
    create_comment(post=post, author=robin, body="A comment written by robin")

    html = member.get("/u/robin/comments/").content.decode()

    assert "A comment written by robin" in html


def test_a_card_shows_number_post_title_date_and_excerpt(member, post, author):
    comment = create_comment(post=post, author=author, body="Some **plain** text, not markdown.")

    card = _cards(member.get(URL).content.decode())[0]

    assert f'href="/posts/{post.pk}/#c-{comment.number}">The Post</a>' in card
    assert f'<span class="comment__number">#{comment.number}</span>' in card
    assert re.search(r"<time datetime=\"[^\"]+\">\d{4}-\d{2}-\d{2}</time>", card)
    assert "Some **plain** text, not markdown." in card  # kein Markdown-Rendering
    assert "<strong>" not in card


def test_a_card_has_exactly_one_link_the_jump_to_the_comment(member, post, author):
    create_comment(post=post, author=author, body="hi")

    card = _cards(member.get(URL).content.decode())[0]

    assert card.count("<a ") == 1


def test_titles_and_text_are_escaped(member, post, author):
    Post.objects.filter(pk=post.pk).update(title="<b>T</b>")
    post.refresh_from_db()
    create_comment(post=post, author=author, body="<script>alert(1)</script>")

    html = member.get(URL).content.decode()

    assert "<b>T</b>" not in html
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in html


def test_a_long_comment_is_shown_as_an_excerpt(member, post, author):
    create_comment(post=post, author=author, body="word " * 100)

    card = _cards(member.get(URL).content.decode())[0]
    excerpt = re.search(r'class="post-card__excerpt">(.*?)</p>', card, re.S).group(1)

    assert len(excerpt) < 100 * 5
    assert excerpt.endswith("…")


# Hüllen und Sichtbarkeit (D-79, FR-B9) --------------------------------------------------


def test_a_deleted_comment_does_not_appear(member, post, author):
    from apps.posts.comments import make_tombstone

    comment = create_comment(post=post, author=author, body="soon gone")
    make_tombstone(comment)

    html = member.get(URL).content.decode()

    assert "soon gone" not in html
    assert _cards(html) == []


def test_a_comment_under_an_invisible_post_does_not_appear(member, post, author, monkeypatch):
    create_comment(post=post, author=author, body="invisible-post-comment-marker")
    monkeypatch.setattr(PostQuerySet, "visible_to", lambda self, profile: self.none())

    html = member.get(URL).content.decode()

    assert "invisible-post-comment-marker" not in html
    assert _cards(html) == []


def test_a_reply_that_becomes_a_tombstone_elsewhere_still_lists_correctly(member, post, author):
    """Der Tab zeigt nur die eigenen Kommentare der Person — eine Antwort auf
    eine fremde Hülle bleibt trotzdem eine normale, eigene Zeile."""
    from apps.posts.comments import make_tombstone

    original = create_comment(post=post, author=author, body="original")
    make_tombstone(original)
    reply = create_comment(post=post, author=author, body="my reply", reply_to=None)

    html = member.get(URL).content.decode()

    assert "my reply" in html
    assert f"#{reply.number}" in html
    assert "original" not in html


# Leerer Zustand --------------------------------------------------------------------------


def test_an_empty_list_says_so_for_the_owner_and_for_others(member, make_profile):
    make_profile("robin")

    own = member.get(URL).content.decode()
    foreign = member.get("/u/robin/comments/").content.decode()

    assert "You haven't written any comments yet." in own
    assert "robin hasn't written any comments yet." in foreign
    assert _cards(own) == [] and _cards(foreign) == []


# Seiten ------------------------------------------------------------------------------------


def test_ten_comments_fit_on_a_page_and_the_rest_goes_on(member, post, author):
    _write(post, author, 25)

    first = member.get(URL).content.decode()
    third = member.get(URL + "?page=3").content.decode()

    assert PAGE_SIZE == 10
    assert len(_cards(first)) == 10 and len(_cards(third)) == 5
    assert _numbers(first)[0] == "25" and _numbers(third)[-1] == "1"
    assert "Page 1 of 3" in first and "Page 3 of 3" in third


def test_an_invalid_page_lands_on_a_real_one(member, post, author):
    _write(post, author, 25)

    assert "Page 1 of 3" in member.get(URL + "?page=0").content.decode()
    assert "Page 3 of 3" in member.get(URL + "?page=99").content.decode()


# Abfragen -------------------------------------------------------------------------------------


def _query_count(client, url):
    with CaptureQueriesContext(connection) as queries:
        client.get(url)
    return len(queries)


def test_more_comments_do_not_cost_more_queries(member, post, author):
    create_comment(post=post, author=author, body="one")
    one = _query_count(member, URL)

    _write(post, author, 8, start=1)
    many = _query_count(member, URL)

    assert many == one


def test_comments_spread_over_different_posts_do_not_cost_more_queries(member, author):
    """`select_related(\"post\")` (für den Titel je Karte) muss auch greifen, wenn
    jeder Kommentar auf einem **anderen** Beitrag steht — sonst eine Abfrage je
    unterschiedlichem Beitrag statt einer gemeinsamen. Bewusst gegen eine feste
    Basis (ein Kommentar) verglichen, nicht gegen den Fall „alle auf demselben
    Beitrag": Ohne `select_related` kostet **jeder Zugriff** auf `.post` eine
    eigene Abfrage, unabhängig davon, ob sich Beiträge wiederholen — dieser
    Vergleich (anders als „gleicher vs. verschiedene Beiträge") schlägt deshalb
    tatsächlich fehl, wenn `select_related` fehlt."""
    solo_post = Post.objects.create(author=author, title="Solo", body="b")
    create_comment(post=solo_post, author=author, body="c")
    one = _query_count(member, URL)

    Comment.objects.all().delete()
    for number in range(5):
        other_post = Post.objects.create(author=author, title=f"Post {number}", body="b")
        create_comment(post=other_post, author=author, body=f"c{number}")
    different_posts_count = _query_count(member, URL)

    assert different_posts_count == one
