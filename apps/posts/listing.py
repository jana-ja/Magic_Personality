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
