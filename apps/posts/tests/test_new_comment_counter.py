"""
Tests für den Zähler neuer Kommentare und Antworten (Task 6.6, FR-B20, D-79).
"""

import re

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext

from apps.posts import seen
from apps.posts.comments import create_comment, make_tombstone
from apps.posts.models import Post, PostSeen

pytestmark = pytest.mark.django_db


@pytest.fixture
def member(gated_client, author):
    gated_client.force_login(author.user)
    return gated_client


@pytest.fixture
def post(author):
    """Ein Beitrag von `author` — dieselbe Person, die `member` einloggt."""
    return Post.objects.create(author=author, title="The Post", body="b")


@pytest.fixture
def robin(make_profile):
    return make_profile("robin")


def _tabs(html):
    return re.search(r'<nav class="profile-tabs".*?</nav>', html, re.S).group(0)


def _cards(html):
    return re.findall(r'<article class="post-card">.*?</article>', html, re.S)


# mark_seen -----------------------------------------------------------------------------


def test_mark_seen_creates_a_row_for_the_post_author(author, post):
    seen.mark_seen(author, post)

    row = PostSeen.objects.get(profile=author, post=post)
    assert row.last_seen_number == post.comment_seq


def test_mark_seen_creates_a_row_for_someone_who_commented(post, robin):
    create_comment(post=post, author=robin, body="hi")

    seen.mark_seen(robin, post)

    assert PostSeen.objects.filter(profile=robin, post=post).exists()


def test_mark_seen_does_nothing_for_an_uninvolved_profile(post, robin):
    """Wer weder Autorin bzw. Autor ist noch selbst kommentiert hat, bekommt
    nie eine Zeile — es gäbe für sie nie eine „neu"-Markierung (FR-B20)."""
    seen.mark_seen(robin, post)

    assert not PostSeen.objects.filter(profile=robin, post=post).exists()


def test_mark_seen_is_a_noop_for_a_guest(post):
    seen.mark_seen(None, post)

    assert not PostSeen.objects.exists()


def test_mark_seen_tracks_the_current_comment_count(author, post, robin):
    create_comment(post=post, author=robin, body="one")
    seen.mark_seen(author, post)
    assert PostSeen.objects.get(profile=author, post=post).last_seen_number == 1

    create_comment(post=post, author=robin, body="two")
    seen.mark_seen(author, post)
    assert PostSeen.objects.get(profile=author, post=post).last_seen_number == 2


# Zählung: was ist "neu" (FR-B20) --------------------------------------------------------


def test_a_new_comment_under_my_post_counts(author, post, robin):
    create_comment(post=post, author=robin, body="new here")

    assert seen.total_new_comment_count(author) == 1
    assert seen.new_counts_by_post(author) == {post.pk: 1}


def test_a_reply_to_my_comment_on_someone_elses_post_counts(author, robin, make_profile):
    other = make_profile("other")
    foreign_post = Post.objects.create(author=other, title="Other's post", body="b")
    mine = create_comment(post=foreign_post, author=author, body="my comment")
    create_comment(post=foreign_post, author=robin, body="a reply", reply_to=mine)

    assert seen.total_new_comment_count(author) == 1
    assert seen.new_counts_by_comment(author) == {mine.pk: 1}


def test_my_own_comments_are_never_counted_as_new(author, post):
    create_comment(post=post, author=author, body="my own comment on my own post")

    assert seen.total_new_comment_count(author) == 0


def test_a_reply_to_someone_elses_comment_on_someone_elses_post_does_not_count(
    author, robin, make_profile
):
    """Weder eigener Beitrag noch eigener Kommentar betroffen — geht `author`
    nichts an (FR-B20)."""
    other = make_profile("other")
    foreign_post = Post.objects.create(author=other, title="Other's post", body="b")
    theirs = create_comment(post=foreign_post, author=other, body="their comment")
    create_comment(post=foreign_post, author=robin, body="a reply to them", reply_to=theirs)

    assert seen.total_new_comment_count(author) == 0


def test_a_tombstoned_comment_does_not_count(author, post, robin):
    """Regression: `.exclude(author=profile)` allein ließe eine Hülle (author=None)
    durch (Django übersetzt das als `NOT (author_id = X AND author_id IS NOT NULL)`,
    was für NULL zutrifft) — `deleted_at__isnull=True` muss das zusätzlich ausschließen."""
    comment = create_comment(post=post, author=robin, body="soon gone")
    make_tombstone(comment)

    assert seen.total_new_comment_count(author) == 0
    assert seen.new_counts_by_post(author) == {}


def test_a_new_comment_that_both_is_under_my_post_and_replies_to_me_counts_once(author, robin):
    """Beide Gründe aus FR-B20 treffen zu (eigener Beitrag **und** Antwort auf
    den eigenen Kommentar) — trotzdem nur eine Zeile in der Zählung."""
    mine_post = Post.objects.create(author=author, title="Mine", body="b")
    my_comment = create_comment(post=mine_post, author=author, body="my comment")
    create_comment(post=mine_post, author=robin, body="a reply", reply_to=my_comment)

    assert seen.total_new_comment_count(author) == 1


def test_a_comment_above_the_watermark_but_by_myself_still_does_not_count(author, post, robin):
    create_comment(post=post, author=robin, body="new")
    seen.mark_seen(author, post)
    create_comment(post=post, author=author, body="my own reply")

    assert seen.total_new_comment_count(author) == 0


# Zurücksetzen durch Öffnen (FR-B20) ------------------------------------------------------


def test_opening_the_post_resets_the_count_for_that_post(member, author, post, robin):
    create_comment(post=post, author=robin, body="new")
    assert seen.total_new_comment_count(author) == 1

    member.get(f"/posts/{post.pk}/")

    assert seen.total_new_comment_count(author) == 0


def test_opening_one_post_does_not_reset_another_posts_count(member, author, post, robin):
    other_post = Post.objects.create(author=author, title="Other", body="b")
    create_comment(post=post, author=robin, body="new on post")
    create_comment(post=other_post, author=robin, body="new on other_post")

    member.get(f"/posts/{post.pk}/")

    counts = seen.new_counts_by_post(author)
    assert counts.get(post.pk, 0) == 0
    assert counts.get(other_post.pk) == 1


def test_commenting_also_counts_as_seeing_the_post(member, author, post, robin):
    create_comment(post=post, author=robin, body="new")
    assert seen.total_new_comment_count(author) == 1

    member.post(f"/posts/{post.pk}/comment/", {"body": "my reply", "reply_to": ""})

    assert seen.total_new_comment_count(author) == 0


# Profil-Tab „Posts": Gesamtabzeichen -----------------------------------------------------


def test_the_posts_tab_shows_the_total_new_count_for_the_owner(member, author, post, robin):
    create_comment(post=post, author=robin, body="new")

    tabs = _tabs(member.get("/u/alex/").content.decode())

    assert '<span class="profile-tabs__count" aria-hidden="true">1</span>' in tabs


def test_no_badge_when_there_are_no_new_comments(member):
    tabs = _tabs(member.get("/u/alex/").content.decode())

    assert "profile-tabs__count" not in tabs


def test_a_visitor_never_sees_someone_elses_new_comment_badge(gated_client, robin, author, post):
    """`new_comment_count` steht nur für die eigene Person im Kontext (D-73-Muster
    wie `friend_request_count`) — eine fremde Person sieht hier nichts, egal, was
    bei `author` „neu" wäre."""
    create_comment(post=post, author=robin, body="new")
    gated_client.force_login(robin.user)

    tabs = _tabs(gated_client.get("/u/alex/").content.decode())

    assert "profile-tabs__count" not in tabs


# Profil-Tab „Posts": Markierung je Karte --------------------------------------------------


def test_a_post_with_new_comments_shows_the_count_on_its_card(member, author, post, robin):
    create_comment(post=post, author=robin, body="new")

    card = _cards(member.get("/u/alex/posts/").content.decode())[0]

    assert '<span class="post-card__new" aria-hidden="true">1 new</span>' in card


def test_a_post_without_new_comments_shows_no_marker(member, author, post):
    card = _cards(member.get("/u/alex/posts/").content.decode())[0]

    assert "post-card__new" not in card


def test_a_foreign_visitor_never_sees_new_markers_on_the_posts_tab(
    gated_client, robin, author, post
):
    create_comment(post=post, author=robin, body="new")
    gated_client.force_login(robin.user)

    html = gated_client.get("/u/alex/posts/").content.decode()

    assert "post-card__new" not in html


# Profil-Tab „Comments": Markierung je Kommentar --------------------------------------------


def test_a_comment_with_new_replies_shows_the_count_on_its_card(
    member, author, robin, make_profile
):
    other = make_profile("other")
    foreign_post = Post.objects.create(author=other, title="Other's post", body="b")
    mine = create_comment(post=foreign_post, author=author, body="my comment")
    create_comment(post=foreign_post, author=robin, body="a reply", reply_to=mine)

    card = _cards(member.get("/u/alex/comments/").content.decode())[0]

    assert '<span class="post-card__new" aria-hidden="true">1 new</span>' in card


def test_a_comment_without_new_replies_shows_no_marker(member, author, post):
    create_comment(post=post, author=author, body="no replies yet")

    card = _cards(member.get("/u/alex/comments/").content.decode())[0]

    assert "post-card__new" not in card


# Abfragen ---------------------------------------------------------------------------------


def _query_count(client, url):
    with CaptureQueriesContext(connection) as queries:
        client.get(url)
    return len(queries)


def test_the_posts_tab_costs_at_most_one_extra_query_for_new_counts(member, author, robin):
    solo_post = Post.objects.create(author=author, title="Solo", body="b")
    create_comment(post=solo_post, author=robin, body="new")
    one = _query_count(member, "/u/alex/posts/")

    Post.objects.exclude(pk=solo_post.pk).delete()
    for number in range(5):
        other_post = Post.objects.create(author=author, title=f"Post {number}", body="b")
        create_comment(post=other_post, author=robin, body=f"new {number}")
    many = _query_count(member, "/u/alex/posts/")

    assert many == one


def test_a_visitors_posts_tab_costs_no_extra_query_for_new_counts(
    gated_client, robin, author, post
):
    """Bei einer fremden Person wird `new_counts_by_post()` gar nicht erst
    aufgerufen (kein `viewer.pk == author.pk`) — die Abfragezahl bleibt gleich,
    ob `author` neue Kommentare hat oder nicht."""
    gated_client.force_login(robin.user)
    without_new = _query_count(gated_client, "/u/alex/posts/")

    create_comment(post=post, author=robin, body="new")
    with_new = _query_count(gated_client, "/u/alex/posts/")

    assert with_new == without_new
