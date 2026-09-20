"""
Tests für die Beitragsseite (Task 5.4, FR-B5, FR-B8, D-78).

Zugriffsschutz (Gate, Login) und „kein Zugriff, wenn `visible_to` nichts
durchlässt" stehen zusätzlich in test_post_editor.py.
"""

import re

import pytest
from django.utils import timezone

from apps.accounts.models import ColorAssignment
from apps.colors.models import ColorCombination
from apps.posts.models import Post

pytestmark = pytest.mark.django_db


@pytest.fixture
def member(gated_client, author):
    gated_client.force_login(author.user)
    return gated_client


def _url(post):
    return f"/posts/{post.pk}/"


def _name(code, name):
    ColorCombination.objects.filter(code=code, locale="en").update(name=name)


def _article(html):
    return re.search(r"<article.*?</article>", html, re.S).group(0)


# Inhalt ------------------------------------------------------------------------------


def test_the_page_shows_title_text_and_the_title_in_the_browser_tab(member, author):
    post = Post.objects.create(author=author, title="A title", body="Some **bold** text")

    html = member.get(_url(post)).content.decode()

    assert "<title>" in html and "A title" in re.search(r"<title>(.*?)</title>", html, re.S).group(
        1
    )
    assert re.search(r'<h1 id="post-title">A title</h1>', html)
    assert "<strong>bold</strong>" in html


def test_there_is_exactly_one_h1_even_if_the_text_has_headings(member, author):
    post = Post.objects.create(author=author, title="T", body="# Big\n\n## Smaller")

    article = _article(member.get(_url(post)).content.decode())

    assert article.count("<h1") == 1
    assert "<h2>Big</h2>" in article
    assert "<h3>Smaller</h3>" in article


def test_title_and_text_are_escaped(member, author):
    post = Post.objects.create(
        author=author, title="<b>Bold</b> & co", body="<script>alert(1)</script>"
    )

    html = member.get(_url(post)).content.decode()

    assert "<b>Bold</b>" not in html
    assert "&lt;b&gt;Bold&lt;/b&gt; &amp; co" in html
    assert "<script>alert(1)</script>" not in html


# Autorenkarte ---------------------------------------------------------------------------


def test_the_author_is_shown_as_an_author_card_linking_to_the_profile(member, author):
    post = Post.objects.create(author=author, title="T", body="b")

    article = _article(member.get(_url(post)).content.decode())

    assert 'class="author-card author-card--medium"' in article
    assert 'href="/u/alex/"' in article
    assert ">alex</a>" in article


def test_the_author_card_shows_the_authors_own_combination(member, author):
    _name("UB", "Dimir")
    ColorAssignment.objects.create(
        profile=author,
        author_profile=author,
        combination=ColorCombination.objects.get(code="UB", locale="en"),
        source=ColorAssignment.Source.SELF_MANUAL,
    )
    post = Post.objects.create(author=author, title="T", body="b")

    article = _article(member.get(_url(post)).content.decode())

    assert '<span class="author-card__chip">Dimir</span>' in article


def test_another_persons_post_shows_that_person_as_the_author(member, make_profile):
    other = make_profile("robin")
    post = Post.objects.create(author=other, title="T", body="b")

    article = _article(member.get(_url(post)).content.decode())

    assert 'href="/u/robin/"' in article
    assert 'href="/u/alex/"' not in article


# Farbverknüpfung --------------------------------------------------------------------------


def test_a_post_with_colors_links_to_its_combination_in_the_color_infos(member, author):
    _name("WG", "Selesnya")
    post = Post.objects.create(author=author, title="T", body="b", colors="WG")

    article = _article(member.get(_url(post)).content.decode())

    assert '<a class="post__combination" href="/colors/wg/">Selesnya</a>' in article
    assert "General" not in article


def test_a_combination_without_a_name_falls_back_to_the_color_names(member, author):
    _name("WG", "")
    post = Post.objects.create(author=author, title="T", body="b", colors="WG")

    article = _article(member.get(_url(post)).content.decode())

    assert 'href="/colors/wg/">White · Green</a>' in article


def test_a_single_color_links_to_its_color_page(member, author):
    post = Post.objects.create(author=author, title="T", body="b", colors="U")

    article = _article(member.get(_url(post)).content.decode())

    assert 'href="/colors/u/"' in article


def test_a_general_post_says_so_and_has_no_color_link(member, author):
    post = Post.objects.create(author=author, title="T", body="b")

    article = _article(member.get(_url(post)).content.decode())

    assert '<span class="post__combination post__combination--general">General</span>' in article
    assert "/colors/" not in article


def test_the_combination_link_leads_to_an_existing_page(member, author):
    post = Post.objects.create(author=author, title="T", body="b", colors="WUBRG")
    article = _article(member.get(_url(post)).content.decode())

    href = re.search(r'class="post__combination" href="([^"]+)"', article).group(1)

    assert member.get(href).status_code == 200


# Datum und „edited" ------------------------------------------------------------------------


def test_the_date_is_shown_as_a_time_element(member, author):
    post = Post.objects.create(author=author, title="T", body="b")

    article = _article(member.get(_url(post)).content.decode())

    assert re.search(r'<time datetime="[\d\-T:+.Z]+">\d{4}-\d{2}-\d{2}</time>', article)
    assert timezone.localtime(post.created_at).strftime("%Y-%m-%d") in article


def test_an_unedited_post_has_no_edited_mark(member, author):
    post = Post.objects.create(author=author, title="T", body="b")

    assert "edited" not in _article(member.get(_url(post)).content.decode())


def test_an_edited_post_shows_when(member, author):
    post = Post.objects.create(author=author, title="T", body="b")
    member.post(f"/posts/{post.pk}/edit/", {"title": "T", "body": "changed"})

    article = _article(member.get(_url(post)).content.decode())

    assert "edited" in article
    assert article.count("<time") == 2


# Aktionen ---------------------------------------------------------------------------------------


def test_edit_and_delete_are_offered_to_the_author_only(member, make_profile, author):
    post = Post.objects.create(author=author, title="T", body="b")
    own = member.get(_url(post)).content.decode()
    member.force_login(make_profile("robin").user)
    foreign = member.get(_url(post)).content.decode()

    for link in (f"/posts/{post.pk}/edit/", f"/posts/{post.pk}/delete/"):
        assert link in own
        assert link not in foreign


# Zugriff ------------------------------------------------------------------------------------------


def test_an_unknown_post_is_404(member):
    assert member.get("/posts/999999/").status_code == 404


def test_only_get_is_allowed(member, author):
    post = Post.objects.create(author=author, title="T", body="b")

    assert member.post(_url(post)).status_code == 405


def test_the_page_needs_a_constant_number_of_queries(member, author, django_assert_max_num_queries):
    post = Post.objects.create(author=author, title="T", body="b", colors="WG")

    with django_assert_max_num_queries(14):
        member.get(_url(post))
