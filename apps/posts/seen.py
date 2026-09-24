"""
Zähler neuer Kommentare und Antworten (Task 6.6, FR-B20, D-79).

„Neu" ist ein Kommentar von jemand anderem, dessen Nummer über dem
zuletzt gesehenen Stand (`PostSeen.last_seen_number`) liegt, und der
entweder unter dem eigenen Beitrag steht oder auf den eigenen Kommentar
antwortet (FR-B20) — Hüllen zählen nicht (D-79: eine Hülle ist kein
Inhalt mehr). Der Stand ist **je Beitrag**, nicht je Kommentar: Öffnen
der Beitragsseite setzt ihn auf den aktuellen `comment_seq` und macht
damit alle Kommentare darunter „gesehen", auch Antworten auf eigene
Kommentare in diesem Beitrag.
"""

from django.db.models import Count, F, OuterRef, Q, Subquery
from django.db.models.functions import Coalesce

from .models import Comment, PostSeen


def mark_seen(profile, post):
    """
    Setzt den gesehenen Stand von `profile` für `post` auf den aktuellen
    `comment_seq` (Task 6.6) — aufgerufen beim Öffnen der Beitragsseite und
    nach dem eigenen Kommentieren.

    Nur für Personen mit einem Grund, den Stand überhaupt zu brauchen: die
    Autorin bzw. der Autor des Beitrags, oder wer selbst schon einen
    Kommentar darunter hat (FR-B20) — sonst gäbe es nie eine
    „neu"-Markierung und die Zeile wäre reine Verschwendung.

    `post.comment_seq` wird zuvor frisch aus der Datenbank nachgeladen
    (`refresh_from_db`), statt dem übergebenen Objekt zu vertrauen: Nach
    `apps.posts.comments.create_comment()` trägt genau dieses Feld an ihrer
    eigenen, gesperrten Kopie des Beitrags den neuen Wert, nicht an der
    Instanz, mit der die Aufruferin (`add_comment`) weiterhin arbeitet — ein
    veralteter Stand würde bereits gesehene Kommentare wieder als „neu"
    zählen. `comment_seq` ist monoton (D-79, Task 6.1): der Stand geht
    dadurch nie zurück, ein `update_or_create` genügt ohne weitere Prüfung.
    """
    if profile is None:
        return
    is_author = post.author_id == profile.id
    if not is_author and not Comment.objects.filter(post=post, author=profile).exists():
        return
    post.refresh_from_db(fields=["comment_seq"])
    PostSeen.objects.update_or_create(
        profile=profile, post=post, defaults={"last_seen_number": post.comment_seq}
    )


def _new_comments(profile):
    """
    Die neuen Kommentare für `profile` über alle Beiträge hinweg — eine
    Abfrage, kein Aufruf je Beitrag (DoD: höchstens eine Zusatzabfrage je
    Seite). Der Wasserstand kommt je Zeile per `Subquery` aus `PostSeen`;
    fehlt eine Zeile (noch nie gesehen), gilt 0 (`Coalesce`).

    `.exclude(author=profile)` lässt bei einem gelöschten Kommentar
    (`author=None`) die Hülle durch — Django übersetzt das `exclude` als
    `NOT (author_id = X AND author_id IS NOT NULL)`, das auf `NULL` nicht
    zutrifft. Das erledigt stattdessen `deleted_at__isnull=True` gleich
    mit: eine Hülle ist ohnehin nie „neu".
    """
    watermark = PostSeen.objects.filter(profile=profile, post=OuterRef("post_id")).values(
        "last_seen_number"
    )[:1]
    return (
        Comment.objects.filter(Q(post__author=profile) | Q(reply_to__author=profile))
        .filter(deleted_at__isnull=True)
        .exclude(author=profile)
        .annotate(watermark=Coalesce(Subquery(watermark), 0))
        .filter(number__gt=F("watermark"))
    )


def total_new_comment_count(profile):
    """Gesamtzahl neuer Kommentare, für das Abzeichen am Reiter „Posts"."""
    if profile is None:
        return 0
    return _new_comments(profile).count()


def new_counts_by_post(profile):
    """`{post_id: Anzahl}` — für die „n neu"-Markierung im Reiter „Posts"."""
    if profile is None:
        return {}
    rows = _new_comments(profile).values("post_id").annotate(n=Count("id")).order_by()
    return {row["post_id"]: row["n"] for row in rows}


def new_counts_by_comment(profile):
    """
    `{comment_id: Anzahl}` — für die „n neu"-Markierung im Reiter
    „Comments": nur Antworten auf den jeweils eigenen Kommentar, unabhängig
    davon, unter wessen Beitrag er steht.
    """
    if profile is None:
        return {}
    rows = (
        _new_comments(profile)
        .filter(reply_to__author=profile)
        .values("reply_to_id")
        .annotate(n=Count("id"))
        .order_by()
    )
    return {row["reply_to_id"]: row["n"] for row in rows}
