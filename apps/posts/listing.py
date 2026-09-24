"""
Seiten mit Beiträgen (Task 5.5, FR-B6; Task 5.6 nutzt dieselben Bausteine),
Kommentaren (Task 6.4, FR-B17) und der Pinnwand (Task 7.2, FR-B22).

Jede Liste liest über `Post.objects.visible_to()` (FR-B9) und bereitet die
Karten so vor, dass eine Seite mit zehn Beiträgen nicht mehr Abfragen kostet
als eine mit einem: eine für die Zählung, eine für die Seite, eine für alle
Kombinationsnamen.
"""

from django.core.paginator import Paginator
from django.db.models import Q

from . import combinations, seen
from .markdown import EXCERPT_LENGTH, truncate_at_word_boundary
from .models import Comment, Pin, Post

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


def cards_for(posts, new_counts=None):
    """
    Für das Template: je Beitrag `{"post", "label", "new_count"}`, `label`
    ist der Kombinationsname oder `None` bei einem allgemeinen Beitrag.
    `new_count` (Task 6.6) ist nur ungleich 0, wenn `new_counts` (von
    `apps.posts.seen.new_counts_by_post()`) mitgegeben wird — also nur auf
    der eigenen Seite „Posts", nicht bei einer fremden.
    """
    posts = list(posts)
    labels = combinations.combination_labels(post.colors for post in posts)
    new_counts = new_counts or {}
    return [
        {
            "post": post,
            "label": labels.get(post.colors),
            "new_count": new_counts.get(post.pk, 0),
        }
        for post in posts
    ]


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

    Die „n neu"-Markierung je Karte (Task 6.6) gibt es nur, wenn `viewer` die
    eigene Seite ansieht (`seen.new_counts_by_post()` sonst gar nicht erst
    aufgerufen) — auf einer fremden Seite gibt es dafür ohnehin nie einen
    Stand.
    """
    posts = Post.objects.visible_to(viewer).filter(author=author)
    page = Paginator(posts, PAGE_SIZE).get_page(page_number(raw_page))
    new_counts = seen.new_counts_by_post(viewer) if viewer.pk == author.pk else None
    return {"posts_page": page, "post_cards": cards_for(page, new_counts)}


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


def comment_excerpt(body):
    """
    Klartext-Auszug eines Kommentars (Task 6.4): Kommentare sind schon
    Klartext (D-80), anders als `apps.posts.markdown.excerpt()` also kein
    Markdown-Parsing nötig — nur Leerraum zusammengezogen und an einer
    Wortgrenze gekürzt, mit derselben Länge wie bei Beiträgen.
    """
    return truncate_at_word_boundary(" ".join(body.split()), EXCERPT_LENGTH)


def author_comments_page(viewer, author, raw_page):
    """
    Eine Seite mit den Kommentaren von `author` (Task 6.4, FR-B17), neueste
    zuerst. Hüllen tauchen nie auf: Sie haben keinen Autor mehr (D-79), fallen
    also schon durch `author=author` heraus. Kommentare unter Beiträgen, die
    `viewer` nicht sehen darf, ebenso — über `Post.objects.visible_to()`
    (FR-B9, D-78), nicht über eine eigene Sichtbarkeitsregel.

    Die „n neu"-Markierung je Kommentar (Task 6.6: neue Antworten auf genau
    diesen Kommentar) gibt es nur auf der eigenen Seite — wie bei
    `author_posts_page()`.
    """
    comments = (
        Comment.objects.filter(author=author, post__in=Post.objects.visible_to(viewer))
        .select_related("post")
        .order_by("-created_at", "-pk")
    )
    page = Paginator(comments, PAGE_SIZE).get_page(page_number(raw_page))
    new_counts = seen.new_counts_by_comment(viewer) if viewer.pk == author.pk else {}
    for comment in page:
        comment.new_count = new_counts.get(comment.pk, 0)
    return {"comments_page": page}


def pinboard_page(viewer, profile, raw_page):
    """
    Eine Seite mit den Pins von `profile` (Task 7.2, FR-B22), zuletzt gepinnt
    zuerst (`Pin.Meta.ordering`). Ein einziges Modell trägt beide Zielarten
    (D-82), eine Abfrage genügt für beide zusammen — kein Zusammenführen
    zweier getrennter Listen in Python.

    Post- wie Kommentar-Pins laufen über `Post.objects.visible_to(viewer)`
    (FR-B9, D-78) — für einen Kommentar-Pin über dessen Beitrag, genau wie
    `author_comments_page()`. Ein gelöschter Beitrag nimmt seinen Pin ohnehin
    mit sich (Kaskade, Task 7.1); ein zur Hülle gewordener Kommentar bleibt
    als Zeile bestehen (D-79) und wird deshalb hier zusätzlich ausgeschlossen
    (`comment__deleted_at__isnull=True`) — sonst gäbe es einen Eintrag ohne
    Autorenkarte. Die volle Sichtbarkeitsprüfung samt eigenem Test (auch für
    eine künftige „nur Freunde"-Regel) ist Aufgabe von Task 7.3.
    """
    pins = (
        Pin.objects.filter(profile=profile)
        .filter(
            Q(post__in=Post.objects.visible_to(viewer))
            | Q(
                comment__post__in=Post.objects.visible_to(viewer),
                comment__deleted_at__isnull=True,
            )
        )
        .select_related("post__author", "comment__author", "comment__post")
        .prefetch_related(
            "post__author__color_assignments__combination",
            "comment__author__color_assignments__combination",
        )
    )
    page = Paginator(pins, PAGE_SIZE).get_page(page_number(raw_page))
    return {"pinboard_page": page}
