"""
Kommentare anlegen (Task 6.1, FR-B14, FR-B15, D-79).

Die **einzige** Stelle, die `Comment`-Zeilen erzeugt — Nummer und `post`
kommen nie von außen, damit die Nummernvergabe nicht umgangen werden kann.

Die Nummer vergibt die Datenbank atomar aus `Post.comment_seq`:
`select_for_update()` sperrt genau diese eine Beitrags-Zeile für die Dauer
der Transaktion, eine zweite, gleichzeitige Anfrage wartet an dieser Sperre,
bis die erste committet hat, und erhöht danach den bereits erhöhten Zähler
weiter — zwei gleichzeitige Kommentare zum selben Beitrag bekommen dadurch
nie dieselbe Nummer. `unique (post, number)` (D-79) ist die zusätzliche
Absicherung in der Datenbank, falls das doch je umgangen würde.

Gesperrt wird über `Post.objects.visible_to(author)` (FR-B9, D-78), nicht
über `Post.objects` direkt: Der View hat die Sichtbarkeit zwar schon vor
dem Aufruf geprüft, aber falls sie sich dazwischen geändert hätte (oder ein
künftiger Aufrufer diese Prüfung vergisst), bricht das hier sauber mit
`Post.DoesNotExist` ab, statt einen Kommentar auf einem inzwischen
unsichtbaren Beitrag anzulegen.
"""

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from .models import Comment, Post


def create_comment(*, post, author, body, reply_to=None):
    """
    Legt einen Kommentar unter `post` an (FR-B13) und gibt ihn zurück.

    `reply_to` (optional) muss ein Kommentar **desselben Beitrags** sein und
    darf keine Hülle sein (FR-B15, D-79) — beides kann kein
    Datenbank-Constraint prüfen (kein Fremdschlüssel über zwei Spalten
    hinweg, und „ist keine Hülle" ist ein Wertevergleich), deshalb prüft es
    dieser Dienst. Die Länge von `body` prüft die Aufruferin (Formular): das
    hier ist reine Zuordnung, keine vollständige Validierung.
    """
    if reply_to is not None:
        if reply_to.post_id != post.pk:
            raise ValidationError(_("You can only reply to a comment on the same post."))
        if reply_to.is_tombstone:
            raise ValidationError(_("You can't reply to a deleted comment."))

    with transaction.atomic():
        locked_post = Post.objects.visible_to(author).select_for_update().get(pk=post.pk)
        locked_post.comment_seq += 1
        locked_post.save(update_fields=["comment_seq"])
        return Comment.objects.create(
            post=locked_post,
            author=author,
            number=locked_post.comment_seq,
            body=body,
            reply_to=reply_to,
        )


def make_tombstone(comment):
    """
    Macht `comment` zur Hülle (Task 6.3, FR-B16, D-79): `deleted_at` gesetzt,
    `body` und `author` geleert — die Zeile selbst bleibt, damit ihre Nummer
    und die „↪ #n"-Verweise anderer Kommentare stabil bleiben. **Die einzige**
    Stelle, die das tut: dieselbe Funktion für das Löschen durch die Autorin
    bzw. den Autor (View `delete_comment`), die Admin-Aktion bei gemeldeten
    Kommentaren (Task 6.5) und die Account-Löschung (`tombstone_comments_by`
    unten).

    Bereits eine Hülle: keine Wirkung, kein Fehler — praktisch für
    `tombstone_comments_by()`, das nicht vorher prüfen muss, ob eine Zeile
    das schon ist.
    """
    if comment.is_tombstone:
        return comment
    comment.deleted_at = timezone.now()
    comment.author = None
    comment.body = ""
    comment.save(update_fields=["deleted_at", "author", "body"])
    return comment


def tombstone_comments_by(profile):
    """
    Macht **jeden** Kommentar von `profile` zur Hülle (FR-B19, Task 6.3) —
    aufzurufen, bevor der Account gelöscht wird: `Comment.author` verweist
    mit `on_delete=PROTECT` auf `Profile` (D-79), das Löschen bräche sonst
    ab, statt eine verwaiste Zeile zu hinterlassen.

    Läuft über **alle** Kommentare der Person, nicht nur die unter fremden
    Beiträgen: Kommentare unter den eigenen Beiträgen verschwinden gleich
    darauf ohnehin mit dem Beitrag selbst (`Post`-Kaskade, FR-B19) — sie
    vorher zur Hülle zu machen ändert daran nichts, erspart hier aber die
    Fallunterscheidung „eigener oder fremder Beitrag". Ein `UPDATE` statt
    `make_tombstone()` je Zeile: kein Fall hier braucht dessen
    Bereits-Hülle-Kurzschluss, eine einzige Anfrage genügt.
    """
    Comment.objects.filter(author=profile, deleted_at__isnull=True).update(
        deleted_at=timezone.now(), author=None, body=""
    )
