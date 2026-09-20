"""
Tests für den Profil-Tab „Posts" (Task 5.5, FR-B6, FR-B8, FR-B9, D-78).
"""

import re

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.utils import timezone

from apps.colors.models import ColorCombination
from apps.posts.listing import PAGE_SIZE
from apps.posts.models import Post

pytestmark = pytest.mark.django_db

URL = "/u/alex/posts/"


@pytest.fixture
def member(gated_client, author):
    gated_client.force_login(author.user)
    return gated_client


def _cards(html):
    return re.findall(r'<article class="post-card">.*?</article>', html, re.S)


def _titles(html):
    return re.findall(r'class="post-card__link" href="[^"]+">([^<]*)</a>', html)


def _tabs(html):
    return re.search(r'<nav class="profile-tabs".*?</nav>', html, re.S).group(0)


def _write(author, count, **overrides):
    """`count` Beiträge mit aufsteigender Zeit: `Post 0` ist der älteste."""
    base = timezone.now() - timezone.timedelta(days=count)
    posts = []
    for number in range(count):
        post = Post.objects.create(author=author, title=f"Post {number}", body="b", **overrides)
        Post.objects.filter(pk=post.pk).update(created_at=base + timezone.timedelta(days=number))
        posts.append(post)
    return posts


# Zugriff ---------------------------------------


def test_the_tab_needs_the_gate_cookie(client):
    response = client.get(URL)

    assert response.status_code == 302
    assert response.url.startswith("/gate/")


def test_the_tab_needs_a_login(gated_client):
    response = gated_client.get(URL)

    assert response.status_code == 302
    assert response.url.startswith("/accounts/login/")


def test_an_unknown_nickname_is_404(member):
    assert member.get("/u/nobody/posts/").status_code == 404


def test_the_nickname_is_matched_case_insensitively(member):
    assert member.get("/u/ALEX/posts/").status_code == 200


# Tab-Leiste -------------------------------------------------------------------------------


def test_every_profile_has_a_posts_tab_between_pinboard_and_friends(member, make_profile):
    make_profile("robin")

    for path in ("/u/alex/", "/u/robin/", "/u/robin/friends/"):
        tabs = _tabs(member.get(path).content.decode())
        assert tabs.index("Pinboard") < tabs.index("Posts") < tabs.index("Friends")


def test_the_posts_tab_is_the_current_page_on_its_own_address(member, make_profile):
    make_profile("robin")

    for nickname in ("alex", "robin"):
        tabs = _tabs(member.get(f"/u/{nickname}/posts/").content.decode())
        assert f'<a href="/u/{nickname}/posts/" aria-current="page">Posts</a>' in tabs
        assert tabs.count("aria-current") == 1


# Liste ---------------------------------------


def test_the_list_shows_this_persons_posts_newest_first(member, author, make_profile):
    _write(author, 3)
    Post.objects.create(author=make_profile("robin"), title="Not mine", body="b")

    html = member.get(URL).content.decode()

    assert _titles(html) == ["Post 2", "Post 1", "Post 0"]
    assert "Not mine" not in html


def test_someone_elses_profile_lists_that_persons_posts(member, make_profile):
    robin = make_profile("robin")
    Post.objects.create(author=robin, title="Robin writes", body="b")

    html = member.get("/u/robin/posts/").content.decode()

    assert "Robin writes" in html
    assert "Write a post" not in html


def test_a_card_shows_title_combination_date_and_a_plain_text_excerpt(member, author):
    ColorCombination.objects.filter(code="WG", locale="en").update(name="Selesnya")
    post = Post.objects.create(
        author=author,
        title="Selesnya thoughts",
        body="# Heading\n\nSome **bold** text with a [link](https://example.com).",
        colors="WG",
    )

    card = _cards(member.get(URL).content.decode())[0]

    assert f'href="/posts/{post.pk}/">Selesnya thoughts</a>' in card
    assert '<span class="post__combination">Selesnya</span>' in card
    assert re.search(r"<time datetime=\"[^\"]+\">\d{4}-\d{2}-\d{2}</time>", card)
    assert "Heading Some bold text with a link." in card
    assert "<strong>" not in card and "<h2" not in card


def test_a_general_post_is_marked_general(member, author):
    Post.objects.create(author=author, title="T", body="b")

    card = _cards(member.get(URL).content.decode())[0]

    assert '<span class="post__combination post__combination--general">General</span>' in card


def test_a_card_contains_exactly_one_link(member, author):
    """Sonst läge ein Link im Link, und Tastatur und Screenreader fänden je
    Beitrag mehrere Ziele."""
    Post.objects.create(
        author=author, title="T", body="[a](https://a.example) [b](https://b.example)"
    )

    for card in _cards(member.get(URL).content.decode()):
        assert card.count("<a ") == 1


def test_a_long_post_is_cut_to_an_excerpt(member, author):
    Post.objects.create(author=author, title="Long", body="word " * 500)

    card = _cards(member.get(URL).content.decode())[0]

    excerpt = re.search(r'<p class="post-card__excerpt">(.*?)</p>', card, re.S).group(1)
    assert len(excerpt) <= 201
    assert excerpt.endswith("…")


def test_titles_and_excerpts_are_escaped(member, author):
    Post.objects.create(author=author, title="<b>T</b>", body="<script>alert(1)</script>")

    html = member.get(URL).content.decode()

    assert "<script>alert(1)</script>" not in html
    assert "<b>T</b>" not in html
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in html


# Seiten ---------------------------------------


def test_ten_posts_fit_on_a_page_and_the_rest_goes_on(member, author):
    _write(author, 25)

    first = member.get(URL).content.decode()
    second = member.get(URL + "?page=2").content.decode()
    third = member.get(URL + "?page=3").content.decode()

    assert PAGE_SIZE == 10
    assert len(_cards(first)) == 10 and len(_cards(second)) == 10 and len(_cards(third)) == 5
    assert _titles(first)[0] == "Post 24" and _titles(third)[-1] == "Post 0"
    assert "Page 1 of 3" in first and "Page 3 of 3" in third


def test_the_page_links_lead_to_the_neighbours(member, author):
    _write(author, 25)

    first = member.get(URL).content.decode()
    second = member.get(URL + "?page=2").content.decode()
    third = member.get(URL + "?page=3").content.decode()

    assert 'href="?page=2" rel="next"' in first and 'rel="prev"' not in first
    assert 'href="?page=1" rel="prev"' in second and 'href="?page=3" rel="next"' in second
    assert 'href="?page=2" rel="prev"' in third and 'rel="next"' not in third


def test_an_invalid_page_lands_on_a_real_one(member, author):
    _write(author, 25)

    assert "Page 3 of 3" in member.get(URL + "?page=99").content.decode()
    assert "Page 1 of 3" in member.get(URL + "?page=abc").content.decode()
    assert "Page 1 of 3" in member.get(URL + "?page=0").content.decode()


def test_ten_posts_or_fewer_show_no_page_links(member, author):
    _write(author, 10)

    assert "pagination" not in member.get(URL).content.decode()


# Eigene Person, leerer Zustand ---------------------------------------


def test_the_owner_can_write_a_post_from_here(member, make_profile):
    make_profile("robin")

    own = member.get(URL).content.decode()
    foreign = member.get("/u/robin/posts/").content.decode()

    assert 'href="/posts/new/"' in own
    assert "/posts/new/" not in foreign


def test_an_empty_list_says_so_for_the_owner_and_for_others(member, make_profile):
    make_profile("robin")

    own = member.get(URL).content.decode()
    foreign = member.get("/u/robin/posts/").content.decode()

    assert "You haven't written anything yet." in own
    assert "Write your first post" in own
    assert "robin hasn't written any posts yet." in foreign
    assert _cards(own) == [] and _cards(foreign) == []


# Sichtbarkeit und Abfragen ---------------------------------------


def test_the_list_reads_through_visible_to(member, author, monkeypatch):
    from apps.posts.models import PostQuerySet

    _write(author, 3)
    monkeypatch.setattr(PostQuerySet, "visible_to", lambda self, profile: self.none())

    html = member.get(URL).content.decode()

    assert _cards(html) == []
    assert "You haven't written anything yet." in html


def _query_count(client, url):
    with CaptureQueriesContext(connection) as queries:
        client.get(url)
    return len(queries)


def test_more_posts_on_a_page_do_not_cost_more_queries(member, author):
    Post.objects.create(author=author, title="One", body="b", colors="WG")
    one = _query_count(member, URL)

    for code in ("U", "B", "R", "G", "WU", "WB", "UBR", "WUBRG", ""):
        Post.objects.create(author=author, title=f"More {code}", body="b", colors=code)
    many = _query_count(member, URL)

    assert many == one


# Löschen führt hierher ---------------------------------------


def test_deleting_a_post_leads_back_to_the_list(member, author):
    post = Post.objects.create(author=author, title="T", body="b")

    response = member.post(f"/posts/{post.pk}/delete/")

    assert response.url == URL
