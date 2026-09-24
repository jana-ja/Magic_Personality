"""
Pinnen und Lösen (Task 7.1, FR-B21, D-82).

Die **einzige** Stelle, die `Pin`-Zeilen anlegt oder löscht — ein einfaches
Umschalten (löschen, sonst anlegen), kein Formular: „Pin"/„Unpin" ist immer
derselbe eine Knopf.
"""

from django.db import IntegrityError, transaction

from .models import Pin


def _toggle(deleted, create):
    """
    Gemeinsamer Ablauf für Beitrag und Kommentar: `deleted` ist die Anzahl
    gelöschter Zeilen (0 oder 1, `UniqueConstraint` erlaubt nie mehr), `create`
    legt die Zeile neu an. Der `IntegrityError`-Fang deckt denselben seltenen
    Fall wie bei Meldungen (`apps.posts.views._process_report`): zwei
    gleichzeitige Klicks sehen beide „noch nicht gepinnt" und versuchen beide
    anzulegen — der zweite verliert gegen den `UniqueConstraint`, landet aber
    trotzdem beim richtigen Endzustand „gepinnt", statt mit einem Fehler
    abzubrechen.
    """
    if deleted:
        return False
    try:
        with transaction.atomic():
            create()
    except IntegrityError:
        pass
    return True


def toggle_post_pin(profile, post):
    """Pinnt `post` für `profile`, oder löst ihn, wenn schon gepinnt. Gibt
    den neuen Zustand zurück (`True` = jetzt gepinnt)."""
    deleted, _ = Pin.objects.filter(profile=profile, post=post).delete()
    return _toggle(deleted, lambda: Pin.objects.create(profile=profile, post=post))


def toggle_comment_pin(profile, comment):
    """Wie `toggle_post_pin()`, für einen Kommentar."""
    deleted, _ = Pin.objects.filter(profile=profile, comment=comment).delete()
    return _toggle(deleted, lambda: Pin.objects.create(profile=profile, comment=comment))
