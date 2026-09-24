"""
Bereitschaft für „nur Freunde" (Task 7.4, PRD §11 v1.5, FR-B9, D-78).

Jeder einzelne Pfad hat schon seinen eigenen Wächtertest verteilt über die
Testdateien der jeweiligen Tasks (`test_post_editor.py`s
`test_every_read_goes_through_visible_to` nennt sich selbst ausdrücklich
„Vorstufe von Task 7.4"). Hier steht die **eine**, zusammenhängende Probe
aus der Roadmap: `Post.objects.visible_to()` durch eine Prüfung ersetzen,
die niemanden mehr durchlässt, und **jeden** Pfad abgehen, der Beiträge
oder Kommentare zeigt — Beitragsseite, Kommentare, Tab „Posts", Tab
„Comments", Grid, Liste je Kombination, Pinnwand, Zähler, Melden, Pinnen.
Ein neuer Lesepfad ohne `visible_to` fiele hier auf, auch wenn er in
keiner der Einzeldateien eigens bedacht wurde.
"""

import pytest

from apps.posts.comments import create_comment
from apps.posts.models import Pin, Post, PostQuerySet
from apps.posts.seen import total_new_comment_count

pytestmark = pytest.mark.django_db


@pytest.fixture
def robin(make_profile):
    return make_profile("robin")


@pytest.fixture
def member(gated_client, author):
    gated_client.force_login(author.user)
    return gated_client


@pytest.fixture
def content(author, robin):
    """
    Beiträge und Kommentare beider Personen, damit jeder Pfad etwas zu
    zeigen hätte, gäbe es `visible_to` nicht: `theirs` (robins Beitrag, mit
    Kombination fürs Grid) trägt `their_comment`; `mine` (author) trägt
    `their_reply_on_mine` von robin — das lässt `total_new_comment_count()`
    für `author` etwas Echtes zählen. `author` pinnt robins Beitrag und
    Kommentar, damit auch die Pinnwand etwas zu verlieren hätte.
    """
    theirs = Post.objects.create(author=robin, title="Robins post", body="b", colors="WG")
    their_comment = create_comment(post=theirs, author=robin, body="Robins comment")
    mine = Post.objects.create(author=author, title="My post", body="b")
    their_reply_on_mine = create_comment(post=mine, author=robin, body="Robin replies to me")
    Pin.objects.create(profile=author, post=theirs)
    Pin.objects.create(profile=author, comment=their_comment)
    return {
        "theirs": theirs,
        "their_comment": their_comment,
        "mine": mine,
        "their_reply_on_mine": their_reply_on_mine,
    }


def test_every_content_path_goes_dark_when_visible_to_is_replaced(
    member, author, robin, content, monkeypatch
):
    theirs = content["theirs"]
    their_comment = content["their_comment"]

    # Vor dem Ersetzen: der Zähler zählt Robins Antwort auf Autors Beitrag —
    # echter Inhalt, den es nachher immer noch geben muss (s. u., „Zähler").
    assert total_new_comment_count(author) == 1

    monkeypatch.setattr(PostQuerySet, "visible_to", lambda self, profile: self.none())

    # Beitragsseite
    assert member.get(f"/posts/{theirs.pk}/").status_code == 404

    # Kommentare: weder ansehen (über dieselbe Seite) noch neu anlegen
    response = member.post(f"/posts/{theirs.pk}/comment/", {"body": "too late", "reply_to": ""})
    assert response.status_code == 404

    # Tab „Posts"
    html = member.get("/u/robin/posts/").content.decode()
    assert "Robins post" not in html

    # Tab „Comments"
    html = member.get("/u/robin/comments/").content.decode()
    assert "Robins comment" not in html

    # Grid (Color Infos zur gewählten Kombination)
    html = member.get("/colors/wg/").content.decode()
    assert "Robins post" not in html

    # Liste je Kombination
    html = member.get("/colors/wg/posts/").content.decode()
    assert "Robins post" not in html

    # Pinnwand
    html = member.get("/u/alex/").content.decode()
    assert "Robins post" not in html
    assert "Robins comment" not in html

    # Zähler: zählt ausschließlich Kommentare unter dem **eigenen** Beitrag
    # bzw. Antworten auf den **eigenen** Kommentar (FR-B20) — beides ist der
    # zählenden Person immer sichtbar, unabhängig von `visible_to`. Bewusst
    # **kein** Rückgang auf 0: Ein Rückgang wäre hier kein Zeichen von mehr
    # Sicherheit, sondern ein Bruch der eigenen Benachrichtigungen.
    assert total_new_comment_count(author) == 1

    # Melden
    assert member.get(f"/posts/{theirs.pk}/report/").status_code == 404
    assert member.get(f"/posts/{theirs.pk}/comments/{their_comment.pk}/report/").status_code == 404

    # Pinnen
    assert member.post(f"/posts/{theirs.pk}/pin/").status_code == 404
    assert member.post(f"/posts/{theirs.pk}/comments/{their_comment.pk}/pin/").status_code == 404
