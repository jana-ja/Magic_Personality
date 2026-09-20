"""
Tests für die Beiträge in den Color Infos (Task 5.6, FR-B7, FR-B8, D-78).
"""

import re

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.utils import timezone

from apps.accounts.models import User
from apps.posts.listing import COMBINATION_PAGE_SIZE, GRID_LIMIT
from apps.posts.models import Post, PostQuerySet

pytestmark = pytest.mark.django_db


@pytest.fixture
def member(gated_client, author):
    gated_client.force_login(author.user)
    return gated_client


def _write(author, count, colors="WG", start=0):
    """`count` Beiträge mit aufsteigender Zeit: der mit der kleinsten Nummer ist der älteste."""
    base = timezone.now() - timezone.timedelta(days=count + start)
    posts = []
    for number in range(start, start + count):
        post = Post.objects.create(
            author=author, title=f"Post {number}", body="Text " * 5, colors=colors
        )
        Post.objects.filter(pk=post.pk).update(created_at=base + timezone.timedelta(days=number))
        posts.append(post)
    return posts


def _grid(html):
    found = re.search(r'<section class="posts-grid".*?</section>', html, re.S)
    return found.group(0) if found else ""


def _titles(html):
    return re.findall(r'class="post-card__link" href="[^"]+">([^<]*)</a>', html)


def _first_card(html):
    return re.search(r'<article class="post-card">.*?</article>', html, re.S).group(0)


def _panel(html):
    return re.search(r'<div id="colors-panel">(.*)</main>', html, re.S).group(1)


# Nur mit Auswahl, im Panel ------------------------------


def test_without_a_selection_there_is_no_grid(member, author):
    _write(author, 3)

    assert _grid(member.get("/colors/").content.decode()) == ""


def test_the_grid_sits_inside_the_panel_that_htmx_swaps(member, author):
    _write(author, 1)

    html = member.get("/colors/wg/").content.decode()

    assert "posts-grid" in _panel(html)
    assert html.index('id="colors-panel"') < html.index("posts-grid") < html.index("<footer")


# Exakter Treffer ------------------------------


def test_only_posts_with_exactly_this_combination_appear(member, author):
    Post.objects.create(author=author, title="WG", body="b", colors="WG")
    Post.objects.create(author=author, title="W", body="b", colors="W")
    Post.objects.create(author=author, title="WGU", body="b", colors="WUG")
    Post.objects.create(author=author, title="General", body="b", colors="")

    assert _titles(_grid(member.get("/colors/wg/").content.decode())) == ["WG"]
    assert _titles(_grid(member.get("/colors/w/").content.decode())) == ["W"]
    assert _titles(_grid(member.get("/colors/wug/").content.decode())) == ["WGU"]


def test_the_order_of_the_selection_does_not_matter(member, author):
    Post.objects.create(author=author, title="WG", body="b", colors="WG")

    response = member.get("/colors/gw/")

    assert response.status_code == 301
    assert response.url == "/colors/wg/"
    assert _titles(_grid(member.get(response.url).content.decode())) == ["WG"]


def test_five_colors_work_too(member, author):
    Post.objects.create(author=author, title="All five", body="b", colors="WUBRG")

    html = member.get("/colors/wubrg/").content.decode()

    assert _titles(_grid(html)) == ["All five"]


def test_posts_of_other_people_appear_too(member, make_profile):
    Post.objects.create(author=make_profile("robin"), title="From robin", body="b", colors="WG")

    assert _titles(_grid(member.get("/colors/wg/").content.decode())) == ["From robin"]


# Menge und Reihenfolge ------------------------------


def test_at_most_six_newest_first_with_a_link_to_all(member, author):
    _write(author, 8)

    grid = _grid(member.get("/colors/wg/").content.decode())

    assert GRID_LIMIT == 6
    assert _titles(grid) == [f"Post {n}" for n in range(7, 1, -1)]
    assert 'href="/colors/wg/posts/"' in grid
    assert "Show all posts" in grid


def test_exactly_six_posts_need_no_link_to_all(member, author):
    _write(author, 6)

    grid = _grid(member.get("/colors/wg/").content.decode())

    assert len(_titles(grid)) == 6
    assert "Show all posts" not in grid


# Karte ------------------------------


def test_a_card_shows_title_author_excerpt_and_date(member, make_profile):
    robin = make_profile("robin")
    post = Post.objects.create(
        author=robin, title="Selesnya", body="Some **bold** words here", colors="WG"
    )

    card = re.search(
        r'<article class="post-card">.*?</article>',
        member.get("/colors/wg/").content.decode(),
        re.S,
    ).group(0)

    assert f'href="/posts/{post.pk}/">Selesnya</a>' in card
    assert 'class="author-card author-card--small"' in card
    assert 'href="/u/robin/"' in card
    assert "Some bold words here" in card
    assert "<strong>" not in card
    assert re.search(r"<time datetime=\"[^\"]+\">\d{4}-\d{2}-\d{2}</time>", card)
    assert "post__combination" not in card  # die Kombination ist ohnehin die gewählte


def test_a_card_has_exactly_two_targets_the_post_and_the_author(member, author):
    post = Post.objects.create(author=author, title="T", body="[x](https://x.example)", colors="WG")

    card = re.search(
        r'<article class="post-card">.*?</article>',
        member.get("/colors/wg/").content.decode(),
        re.S,
    ).group(0)

    assert re.findall(r'<a [^>]*href="([^"]+)"', card) == [f"/posts/{post.pk}/", "/u/alex/"]


def test_titles_and_excerpts_are_escaped(member, author):
    Post.objects.create(
        author=author, title="<b>T</b>", body="<script>alert(1)</script>", colors="WG"
    )

    html = member.get("/colors/wg/").content.decode()

    assert "<script>alert(1)</script>" not in html
    assert "<b>T</b>" not in html


# Leer, Gäste, Sonderfälle ------------------------------


def test_an_empty_combination_invites_to_write_the_first_post(member):
    grid = _grid(member.get("/colors/wg/").content.decode())

    assert "No posts about this combination yet." in grid
    assert 'href="/posts/new/?colors=wg"' in grid
    assert "post-grid" not in grid


def test_the_write_link_carries_the_colors_and_opens_the_prefilled_editor(member):
    grid = _grid(member.get("/colors/wg/").content.decode())
    href = re.search(r'class="posts-head__write tap-target" href="([^"]+)"', grid).group(1)

    response = member.get(href)

    assert href == "/posts/new/?colors=wg"
    assert response.status_code == 200
    assert response.context["form"].initial["colors"] == ["G", "W"]


def test_guests_see_only_a_login_hint_and_no_post(gated_client, author):
    _write(author, 3)

    html = gated_client.get("/colors/wg/").content.decode()
    grid = _grid(html)

    assert "Log in to read and write posts." in grid
    assert 'href="/accounts/login/?next=/colors/wg/"' in grid
    assert "Post 0" not in html and "Post 2" not in html
    assert "post-card" not in html
    assert "/posts/new/" not in grid
    assert "Show all posts" not in grid


def test_a_guest_without_a_selection_sees_nothing_about_posts(gated_client, author):
    _write(author, 3)

    assert "posts-grid" not in gated_client.get("/colors/").content.decode()


def test_an_account_without_a_profile_gets_the_page_without_the_grid(gated_client, author):
    _write(author, 3)
    user = User.objects.create_user(email="noprofile@example.com", password="a-long-enough-pw")
    gated_client.force_login(user)

    response = gated_client.get("/colors/wg/")

    assert response.status_code == 200
    assert "posts-grid" not in response.content.decode()


def test_the_grid_reads_through_visible_to(member, author, monkeypatch):
    _write(author, 3)
    monkeypatch.setattr(PostQuerySet, "visible_to", lambda self, profile: self.none())

    grid = _grid(member.get("/colors/wg/").content.decode())

    assert "No posts about this combination yet." in grid
    assert _titles(grid) == []


def _query_count(client, url):
    with CaptureQueriesContext(connection) as queries:
        client.get(url)
    return len(queries)


def test_more_cards_do_not_cost_more_queries(member, author, make_profile):
    _write(author, 1)
    one = _query_count(member, "/colors/wg/")

    for name in ("robin", "sam", "kai", "lee", "max"):
        Post.objects.create(author=make_profile(name), title=name, body="b", colors="WG")
    six = _query_count(member, "/colors/wg/")

    assert six == one


# Alle Beiträge ------------------------------


def test_the_list_page_needs_the_gate_and_a_login(client):
    assert client.get("/colors/wg/posts/").url.startswith("/gate/")


def test_the_list_page_sends_guests_to_the_login(gated_client):
    response = gated_client.get("/colors/wg/posts/")

    assert response.status_code == 302
    assert response.url.startswith("/accounts/login/")


def test_the_list_page_rejects_invalid_codes_and_redirects_to_the_canonical_form(member):
    assert member.get("/colors/xx/posts/").status_code == 404
    assert member.get("/colors/wwg/posts/").status_code == 404

    response = member.get("/colors/GW/posts/")

    assert response.status_code == 301
    assert response.url == "/colors/wg/posts/"


def test_the_list_page_has_twelve_per_page_newest_first(member, author):
    _write(author, 30)
    _write(author, 4, colors="W", start=100)  # andere Kombination

    first = member.get("/colors/wg/posts/").content.decode()
    third = member.get("/colors/wg/posts/?page=3").content.decode()

    assert COMBINATION_PAGE_SIZE == 12
    assert len(_titles(first)) == 12 and len(_titles(third)) == 6
    assert _titles(first)[0] == "Post 29"
    assert "Post 10" not in third and _titles(third)[-1] == "Post 0"
    assert "Page 1 of 3" in first
    assert 'href="?page=2" rel="next"' in first


def test_the_list_page_links_back_and_offers_to_write(member, author):
    _write(author, 1)

    html = member.get("/colors/wg/posts/").content.decode()

    assert 'href="/colors/wg/"' in html and "Back to Color Infos" in html
    assert 'href="/posts/new/?colors=wg"' in html
    assert "<h1>Posts about White · Green</h1>" in html


def test_an_empty_list_page_says_so(member):
    html = member.get("/colors/wg/posts/").content.decode()

    assert "No posts about this combination yet." in html
    assert "post-card" not in html


def test_the_list_page_reads_through_visible_to(member, author, monkeypatch):
    _write(author, 3)
    monkeypatch.setattr(PostQuerySet, "visible_to", lambda self, profile: self.none())

    assert _titles(member.get("/colors/wg/posts/").content.decode()) == []
