"""
Tests für den Pinnwand-Tab (Task 7.2, FR-B22, D-82).

Das Pinnen selbst (`Pin`, Datenbank-Constraints, Kaskade) deckt
`test_pins.py` ab (Task 7.1); hier geht es um die Liste: Reihenfolge, die
Karte je Eintrag, eigenes vs. fremdes Profil und den leeren Zustand.
"""

import re

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.utils import timezone

from apps.posts.comments import create_comment
from apps.posts.listing import PAGE_SIZE
from apps.posts.models import Pin, Post

pytestmark = pytest.mark.django_db

URL = "/u/alex/"


@pytest.fixture
def member(gated_client, author):
    gated_client.force_login(author.user)
    return gated_client


@pytest.fixture
def robin(make_profile):
    return make_profile("robin")


@pytest.fixture
def post(robin):
    """Ein fremder Beitrag — `alex` (der angemeldete `member`) pinnt ihn."""
    return Post.objects.create(author=robin, title="Robin's post", body="Some body text")


@pytest.fixture
def comment(post, robin):
    return create_comment(post=post, author=robin, body="A comment worth pinning")


def _pin(profile, *, post=None, comment=None, when=None):
    pin = Pin.objects.create(profile=profile, post=post, comment=comment)
    if when is not None:
        Pin.objects.filter(pk=pin.pk).update(created_at=when)
        pin.refresh_from_db()
    return pin


def _cards(html):
    return re.findall(r'<article class="post-card">.*?</article>', html, re.S)


def _kinds(html):
    return re.findall(r'<span class="pin-card__kind">([^<]*)</span>', html)


# Reihenfolge --------------------------------------------------------------------------------


def test_pins_are_shown_newest_pin_first(member, author, robin):
    first = Post.objects.create(author=robin, title="First pinned", body="b")
    second = Post.objects.create(author=robin, title="Second pinned", body="b")
    base = timezone.now() - timezone.timedelta(days=2)
    _pin(author, post=first, when=base)
    _pin(author, post=second, when=base + timezone.timedelta(days=1))

    html = member.get(URL).content.decode()

    titles = re.findall(r'class="post-card__link"[^>]*>([^<]*)</a>', html)
    assert titles == ["Second pinned", "First pinned"]


# Karte je Eintrag ------------------------------------------------------------------------------


def test_a_pinned_post_shows_kind_author_excerpt_date_and_link(member, author, robin, post):
    _pin(author, post=post)

    card = _cards(member.get(URL).content.decode())[0]

    assert "Post" in _kinds(card)
    assert "robin" in card  # Autorenkarte des Originals, nicht der pinnenden Person
    assert "Some body text" in card  # Auszug
    assert re.search(r"<time datetime=\"[^\"]+\">\d{4}-\d{2}-\d{2}</time>", card)
    assert f'href="/posts/{post.pk}/"' in card


def test_a_pinned_comment_shows_kind_and_jumps_to_its_anchor(member, author, robin, post, comment):
    _pin(author, comment=comment)

    card = _cards(member.get(URL).content.decode())[0]

    assert "Comment" in _kinds(card)
    assert "robin" in card
    assert "A comment worth pinning" in card
    assert f'href="/posts/{post.pk}/#c-{comment.number}"' in card
    assert "Robin&#x27;s post" in card  # Titel des Beitrags, nicht der Kommentar selbst


def test_a_pinned_own_post_still_shows_its_author_card(member, author):
    mine = Post.objects.create(author=author, title="My own post", body="b")
    _pin(author, post=mine)

    card = _cards(member.get(URL).content.decode())[0]

    assert ">alex<" in card


# Eigenes vs. fremdes Profil ----------------------------------------------------------------


def test_unpin_is_shown_only_on_the_own_pinboard(member, gated_client, author, robin, post):
    _pin(author, post=post)

    own = member.get(URL).content.decode()
    gated_client.force_login(robin.user)
    foreign = gated_client.get("/u/alex/").content.decode()

    assert "Unpin" in _cards(own)[0]
    assert "Unpin" not in _cards(foreign)[0]
    assert "<form" not in _cards(foreign)[0]


def test_a_foreign_profiles_own_pins_are_shown(member, author, robin):
    theirs = Post.objects.create(author=author, title="Something robin likes", body="b")
    _pin(robin, post=theirs)

    html = member.get("/u/robin/").content.decode()

    assert "Something robin likes" in html


def test_unpinning_from_the_pinboard_removes_it(member, author, post):
    pin = _pin(author, post=post)

    member.post(f"/posts/{post.pk}/pin/")

    assert not Pin.objects.filter(pk=pin.pk).exists()


# Unpin von der Pinnwand aus: die ganze Karte verschwindet, nicht nur die Beschriftung -------


def test_unpinning_a_post_via_htmx_from_the_pinboard_returns_an_empty_response(
    member, author, post
):
    """Anders als auf der Beitragsseite: dort tauscht derselbe Knopf nur seine
    Beschriftung (`_post_pin.html`), weil das Ziel sichtbar bleibt; hier zeigt
    die Liste nur Gepinntes, eine leere Antwort lässt htmx die ganze Karte
    entfernen (`hx-target="closest .post-card"`)."""
    _pin(author, post=post)

    response = member.post(
        f"/posts/{post.pk}/pin/", {"context": "pinboard"}, **{"HTTP_HX_REQUEST": "true"}
    )

    assert response.status_code == 200
    assert response.content == b""


def test_unpinning_a_comment_via_htmx_from_the_pinboard_returns_an_empty_response(
    member, author, post, comment
):
    _pin(author, comment=comment)

    response = member.post(
        f"/posts/{post.pk}/comments/{comment.pk}/pin/",
        {"context": "pinboard"},
        **{"HTTP_HX_REQUEST": "true"},
    )

    assert response.status_code == 200
    assert response.content == b""


def test_unpinning_without_javascript_from_the_pinboard_redirects_back_to_it(member, author, post):
    """Ohne JavaScript käme man sonst auf die Beitragsseite (`pin_post()`s
    üblicher Fall) — von der eigenen Pinnwand aus geht es zurück dorthin."""
    _pin(author, post=post)

    response = member.post(f"/posts/{post.pk}/pin/", {"context": "pinboard"})

    assert response.status_code == 302
    assert response.url == "/u/alex/"


def test_a_plain_pin_click_without_the_pinboard_context_is_unaffected(member, author, post):
    """Der Beitragsseiten-Knopf schickt kein `context`-Feld mit — die
    Pinnwand-Sonderbehandlung greift dann nicht (Gegenprobe zur eigenen
    Erkennung in `_pinboard_unpin_response()`)."""
    _pin(author, post=post)

    response = member.post(f"/posts/{post.pk}/pin/", **{"HTTP_HX_REQUEST": "true"})

    assert response.content != b""
    assert b"Pin" in response.content


# Leerer Zustand ------------------------------------------------------------------------------


def test_an_empty_pinboard_says_so_for_the_owner_and_for_others(member, robin):
    own = member.get(URL).content.decode()
    foreign = member.get("/u/robin/").content.decode()

    assert "haven't pinned anything yet" in own
    assert "Nothing pinned yet." in foreign
    assert _cards(own) == [] and _cards(foreign) == []


# Seiten ----------------------------------------------------------------------------------------


def test_ten_pins_fit_on_a_page_and_the_rest_goes_on(member, author, robin):
    base = timezone.now() - timezone.timedelta(days=25)
    for number in range(25):
        target = Post.objects.create(author=robin, title=f"Post {number}", body="b")
        _pin(author, post=target, when=base + timezone.timedelta(days=number))

    first = member.get(URL).content.decode()
    third = member.get(URL + "?page=3").content.decode()

    assert PAGE_SIZE == 10
    assert len(_cards(first)) == 10 and len(_cards(third)) == 5
    assert "Page 1 of 3" in first and "Page 3 of 3" in third


# Hüllen (Vorgriff auf die volle Sichtbarkeitsprüfung in Task 7.3) --------------------------


def test_a_tombstoned_pinned_comment_does_not_crash_or_appear(member, author, post, comment):
    from apps.posts.comments import make_tombstone

    _pin(author, comment=comment)
    make_tombstone(comment)

    response = member.get(URL)

    assert response.status_code == 200
    assert _cards(response.content.decode()) == []


# Abfragen ----------------------------------------------------------------------------------


def _query_count(client, url):
    with CaptureQueriesContext(connection) as queries:
        client.get(url)
    return len(queries)


def _pin_one_of_each_kind(author, robin):
    """Ein Post-Pin und ein Kommentar-Pin — dieselbe Mischung wie in `many`
    unten, damit der Vergleich tatsächlich die Anzahl der Pins testet, nicht
    (zusätzlich) ob überhaupt beide Arten vorkommen: Ein `prefetch_related()`
    auf eine leere Art (z. B. keine Kommentar-Pins) stellt Django schon selbst
    zurück, ohne eigene Abfrage — ein Vergleich „nur Beiträge" gegen „gemischt"
    würde also fälschlich eine zusätzliche Abfrage melden."""
    post = Post.objects.create(author=robin, title="Solo post", body="b")
    _pin(author, post=post)
    comment = create_comment(post=post, author=robin, body="solo comment")
    _pin(author, comment=comment)


def test_more_pins_do_not_cost_more_queries(member, author, robin):
    _pin_one_of_each_kind(author, robin)
    one = _query_count(member, URL)

    Pin.objects.all().delete()
    for _ in range(4):
        _pin_one_of_each_kind(author, robin)

    many = _query_count(member, URL)

    assert many == one
