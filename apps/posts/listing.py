"""
Seiten mit Beiträgen (Task 5.5, FR-B6; Task 5.6 nutzt dieselben Bausteine).

Jede Liste liest über `Post.objects.visible_to()` (FR-B9) und bereitet die
Karten so vor, dass eine Seite mit zehn Beiträgen nicht mehr Abfragen kostet
als eine mit einem: eine für die Zählung, eine für die Seite, eine für alle
Kombinationsnamen.
"""

from django.core.paginator import Paginator

from . import combinations
from .models import Post

PAGE_SIZE = 10
#: So viele Beiträge zeigt das Grid der Color Infos höchstens (FR-B7); alle stehen auf der
#: Listenseite.
GRID_LIMIT = 6
#: Beiträge je Seite der Liste zu einer Kombination (Task 5.6).
COMBINATION_PAGE_SIZE = 12


def _with_authors(posts):
    """Autorin bzw. Autor samt Zuordnung und Kombination vorladen: die Autorenkarte
    (Task 4.8) kostet dann je Karte keine Abfrage mehr."""
    return posts.select_related("author").prefetch_related("author__color_assignments__combination")


def cards_for(posts):
    """Für das Template: je Beitrag `{"post", "label"}`, `label` ist der
    Kombinationsname oder `None` bei einem allgemeinen Beitrag."""
    posts = list(posts)
    labels = combinations.combination_labels(post.colors for post in posts)
    return [{"post": post, "label": labels.get(post.colors)} for post in posts]


def page_number(raw):
    """Die Seitennummer aus `?page=`: alles, was keine Zahl über null ist, ergibt
    Seite 1 (Djangos `get_page` schickte `0` und Negatives auf die letzte Seite)."""
    try:
        return max(int(raw), 1)
    except (TypeError, ValueError):
        return 1


def author_posts_page(viewer, author, raw_page):
    """
    Eine Seite mit den Beiträgen von `author`, die `viewer` sehen darf, neueste
    zuerst (Task 5.5). Eine ungültige Seitennummer landet freundlich auf der
    ersten, eine zu große auf der letzten Seite statt auf einem Fehler.
    """
    posts = Post.objects.visible_to(viewer).filter(author=author)
    page = Paginator(posts, PAGE_SIZE).get_page(page_number(raw_page))
    return {"posts_page": page, "post_cards": cards_for(page)}


def combination_grid(viewer, code):
    """
    Die neuesten Beiträge mit **genau** dem Farbcode `code` für das Grid der Color
    Infos (Task 5.6, FR-B7): höchstens `GRID_LIMIT`, dazu, ob es weitere gibt.
    Kein Teilmengen-Treffer: ein Beitrag zu `WG` erscheint nicht bei `W` und nicht
    bei `WGU` (D-78).
    """
    posts = list(
        _with_authors(Post.objects.visible_to(viewer).filter(colors=code))[: GRID_LIMIT + 1]
    )
    return {"grid_posts": posts[:GRID_LIMIT], "grid_has_more": len(posts) > GRID_LIMIT}


def combination_posts_page(viewer, code, raw_page):
    """Eine Seite mit allen Beiträgen zu `code` (Task 5.6), neueste zuerst."""
    posts = _with_authors(Post.objects.visible_to(viewer).filter(colors=code))
    page = Paginator(posts, COMBINATION_PAGE_SIZE).get_page(page_number(raw_page))
    return {"posts_page": page, "grid_posts": list(page)}
