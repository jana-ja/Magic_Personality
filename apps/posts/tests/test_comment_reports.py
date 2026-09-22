"""
Tests für das Melden von Kommentaren (Task 6.5, FR-B10, FR-B18, D-81).

`test_reports.py` deckt das Melden von Beiträgen vollständig ab; hier geht
es um das, was bei Kommentaren anders ist: das zweite Ziel-Feld auf
`Report`, die gemeinsame Grenze mit Beiträgen, und dass eine Meldung eine
Hülle überlebt (anders als ein gelöschter Beitrag).
"""

import pytest
from django.conf import settings
from django.db import IntegrityError, transaction

from apps.accounts.models import Profile, User
from apps.posts.comments import create_comment, make_tombstone
from apps.posts.models import Comment, Post, PostQuerySet, Report

pytestmark = pytest.mark.django_db

HTMX = {"HTTP_HX_REQUEST": "true"}


@pytest.fixture
def robin(make_profile):
    return make_profile("robin")


@pytest.fixture
def post(robin):
    """Ein Beitrag von robin; `alex` (der angemeldete `member`) ist fremd."""
    return Post.objects.create(author=robin, title="Robin's post", body="Text")


@pytest.fixture
def comment(post, robin):
    """Ein Kommentar von robin unter ihrem eigenen Beitrag."""
    return create_comment(post=post, author=robin, body="Robin's comment")


@pytest.fixture
def member(gated_client, author):
    gated_client.force_login(author.user)
    return gated_client


def _url(post, comment):
    return f"/posts/{post.pk}/comments/{comment.pk}/report/"


# Zugriff -----------------------------------------------------------------------------


def test_reporting_needs_the_gate(client, post, comment):
    response = client.get(_url(post, comment))

    assert response.status_code == 302
    assert response.url.startswith("/gate/")


def test_guests_are_sent_to_the_login(gated_client, post, comment):
    for response in (
        gated_client.get(_url(post, comment)),
        gated_client.post(_url(post, comment), {"reason": "x"}),
    ):
        assert response.status_code == 302
        assert response.url.startswith("/accounts/login/")
    assert Report.objects.count() == 0


def test_an_unknown_comment_is_404(member, post):
    assert member.get(f"/posts/{post.pk}/comments/999999/report/").status_code == 404
    assert member.post(f"/posts/{post.pk}/comments/999999/report/", {}).status_code == 404


def test_a_mismatched_post_and_comment_is_404(member, author, comment):
    other_post = Post.objects.create(author=author, title="Other", body="b")

    assert member.get(f"/posts/{other_post.pk}/comments/{comment.pk}/report/").status_code == 404


def test_a_post_that_is_not_visible_cannot_be_reported(member, post, comment, monkeypatch):
    monkeypatch.setattr(PostQuerySet, "visible_to", lambda self, profile: self.none())

    assert member.get(_url(post, comment)).status_code == 404
    assert member.post(_url(post, comment), {}).status_code == 404
    assert Report.objects.count() == 0


def test_only_get_and_post_are_allowed(member, post, comment):
    assert member.put(_url(post, comment)).status_code == 405


# Der eigene Kommentar und Hüllen ------------------------------------------------------


def test_your_own_comment_cannot_be_reported(member, post, author):
    own = create_comment(post=post, author=author, body="Mine")

    got = member.get(_url(post, own))
    posted = member.post(_url(post, own), {"reason": "spam"})

    for response in (got, posted):
        assert response.status_code == 302
        assert response.url == f"/posts/{post.pk}/"
    assert Report.objects.count() == 0


def test_a_tombstone_cannot_be_reported(member, post, robin):
    tombstone = create_comment(post=post, author=robin, body="soon gone")
    create_comment(post=post, author=robin, body="a reply", reply_to=tombstone)
    make_tombstone(tombstone)

    response = member.post(_url(post, tombstone), {"reason": "x"})

    assert response.status_code == 302
    assert Report.objects.count() == 0


def test_the_comment_offers_reporting_only_for_other_peoples_comments(member, author, post):
    foreign = create_comment(post=post, author=post.author, body="theirs")
    own = create_comment(post=post, author=author, body="mine")

    html = member.get(f"/posts/{post.pk}/").content.decode()

    assert f'href="{_url(post, foreign)}"' in html
    assert f'hx-get="{_url(post, foreign)}"' in html
    assert f'id="report-comment-{foreign.pk}"' in html
    assert f'id="report-comment-{own.pk}"' not in html


# Formular ------------------------------------------------------------------------------


def test_the_report_page_shows_the_form_without_javascript(member, post, comment):
    html = member.get(_url(post, comment)).content.decode()

    assert "Report comment" in html
    assert f"comment #{comment.number}" in html
    assert 'name="reason"' in html
    assert "Nothing happens automatically." in html
    assert f'action="{_url(post, comment)}"' in html


def test_htmx_gets_only_the_form_fragment(member, post, comment):
    html = member.get(_url(post, comment), **HTMX).content.decode()

    assert "<html" not in html
    assert 'name="reason"' in html


# Melden ----------------------------------------------------------------------------------


def test_a_report_is_stored_with_reporter_comment_and_reason(member, author, post, comment):
    response = member.post(_url(post, comment), {"reason": "  This is spam.  "})

    report = Report.objects.get()
    assert response.status_code == 302
    assert response.url == f"{_url(post, comment)}thanks/"
    assert (report.reporter, report.comment, report.post) == (author, comment, None)
    assert report.reason == "This is spam."
    assert report.target == comment


def test_the_thanks_page_confirms_after_a_report(member, post, comment):
    member.post(_url(post, comment), {"reason": "x"})

    html = member.get(f"{_url(post, comment)}thanks/").content.decode()

    assert "Thank you, we will look at it." in html


def test_the_thanks_page_without_a_report_leads_back_to_the_form(member, post, comment):
    response = member.get(f"{_url(post, comment)}thanks/")

    assert response.status_code == 302
    assert response.url == _url(post, comment)


def test_htmx_returns_only_the_thanks_fragment(member, post, comment):
    response = member.post(_url(post, comment), {"reason": "x"}, **HTMX)

    html = response.content.decode()
    assert response.status_code == 200
    assert "<html" not in html
    assert "Thank you, we will look at it." in html
    assert Report.objects.count() == 1


def test_a_rejected_reason_is_shown_again_escaped(member, post, comment):
    body = "<script>alert(1)</script>" * 30
    html = member.post(_url(post, comment), {"reason": body}).content.decode()

    assert "<script>alert(1)</script>" not in html


# Einmal je Person und Kommentar ---------------------------------------------------------


def test_reporting_twice_creates_no_second_report(member, post, comment):
    member.post(_url(post, comment), {"reason": "first"})

    again = member.post(_url(post, comment), {"reason": "second"})

    assert again.status_code == 200
    assert "You have already reported this comment." in again.content.decode()
    assert Report.objects.get().reason == "first"


def test_the_form_is_replaced_by_a_note_once_reported(member, post, comment):
    member.post(_url(post, comment), {"reason": "x"})

    page = member.get(_url(post, comment)).content.decode()
    detail = member.get(f"/posts/{post.pk}/").content.decode()

    assert "You have already reported this comment." in page and 'name="reason"' not in page
    assert "You have reported this comment." in detail


def test_the_database_allows_one_report_per_person_and_comment(author, comment):
    Report.objects.create(reporter=author, comment=comment)

    with pytest.raises(IntegrityError), transaction.atomic():
        Report.objects.create(reporter=author, comment=comment)


def test_reporting_the_same_post_and_one_of_its_comments_is_two_separate_reports(
    member, author, post, comment
):
    """`post` und `comment` teilen sich keinen Unique-Constraint — eine Person
    darf denselben Beitrag **und** einen seiner Kommentare melden."""
    member.post(f"/posts/{post.pk}/report/", {"reason": "post"})
    member.post(_url(post, comment), {"reason": "comment"})

    assert Report.objects.count() == 2


def test_one_person_can_report_several_comments(member, post, robin):
    first = create_comment(post=post, author=robin, body="one")
    second = create_comment(post=post, author=robin, body="two")

    member.post(_url(post, first), {})
    member.post(_url(post, second), {})

    assert Report.objects.count() == 2


# Genau eines von post/comment (Datenbank-Constraint, D-81) -------------------------------


def test_the_database_requires_exactly_one_target(author, post, comment):
    with pytest.raises(IntegrityError), transaction.atomic():
        Report.objects.create(reporter=author, post=post, comment=comment)

    with pytest.raises(IntegrityError), transaction.atomic():
        Report.objects.create(reporter=author)


# Grenze, gemeinsam mit Beiträgen (FR-B11/FR-B18) ------------------------------------------


def _fill_up_the_limit_with_post_reports(reporter, robin):
    for number in range(settings.REPORT_RATE_LIMIT_MAX_REPORTS):
        target = Post.objects.create(author=robin, title=f"P{number}", body="b")
        Report.objects.create(reporter=reporter, post=target)


def _fill_up_the_limit_with_comment_reports(reporter, post, robin):
    for number in range(settings.REPORT_RATE_LIMIT_MAX_REPORTS):
        target = create_comment(post=post, author=robin, body=f"c{number}")
        Report.objects.create(reporter=reporter, comment=target)


def test_post_reports_count_toward_the_comment_limit(member, author, robin, post, comment):
    _fill_up_the_limit_with_post_reports(author, robin)

    response = member.post(_url(post, comment), {"reason": "one too many"})

    assert response.status_code == 429
    assert "reporting too fast" in response.content.decode()
    assert Report.objects.filter(comment=comment).count() == 0


def test_comment_reports_count_toward_the_post_limit(member, author, robin, post):
    _fill_up_the_limit_with_comment_reports(author, post, robin)

    response = member.post(f"/posts/{post.pk}/report/", {"reason": "one too many"})

    assert response.status_code == 429
    assert Report.objects.filter(post=post).count() == 0


def test_the_limit_message_is_visible_with_htmx_too(member, author, robin, post, comment):
    _fill_up_the_limit_with_post_reports(author, robin)

    response = member.post(_url(post, comment), {"reason": "x"}, **HTMX)

    assert response.status_code == 200
    assert "reporting too fast" in response.content.decode()


# Aufräumen — und eine Hülle, anders als ein gelöschter Beitrag, räumt nicht auf (D-81) ----


def test_a_report_disappears_when_the_whole_post_is_deleted(author, post, comment):
    Report.objects.create(reporter=author, comment=comment)

    post.delete()

    assert Report.objects.count() == 0


def test_a_report_disappears_with_the_reporters_account(author, comment):
    Report.objects.create(reporter=author, comment=comment)

    author.user.delete()

    assert Report.objects.count() == 0
    assert Comment.objects.filter(pk=comment.pk).exists()


def test_a_report_survives_the_comment_becoming_a_tombstone(author, post, robin, comment):
    """Anders als ein gelöschter Beitrag: Eine Hülle ist immer noch dieselbe Zeile
    (D-79), die Meldung dazu bleibt also bestehen, bis die Projektinhaberin sie
    im Admin bearbeitet."""
    # die Antwort hält die Hülle später sichtbar; für diesen Test nicht nötig, aber realistisch
    create_comment(post=post, author=robin, body="a reply", reply_to=comment)
    Report.objects.create(reporter=author, comment=comment)

    make_tombstone(comment)

    assert Report.objects.count() == 1
    report = Report.objects.get()
    assert report.comment_id == comment.pk
    assert report.target.is_tombstone


def test_a_report_survives_the_comment_authors_account_being_deleted(
    gated_client, author, post, robin
):
    """`tombstone_comments_by()` (Task 6.3) leert nur `author`/`body` der Zeile —
    die Zeile selbst und damit die Meldung bleiben bestehen. `post` gehört
    `robin`, der gemeldete Kommentar `author` (alex): löscht **alex** den
    eigenen Account, bleibt `robin`s Beitrag unberührt, der Kommentar wird
    nur zur Hülle (nicht hart entfernt, anders als beim vorigen Test — dort
    gehörte der Beitrag der gelöschten Person selbst). Über den echten Weg
    (`/accounts/delete/`): `Comment.author` ist `PROTECT` (D-79), ein
    direkter `author.user.delete()` ohne den vorherigen
    `tombstone_comments_by()`-Schritt der View bräche mit `ProtectedError` ab."""
    own_comment = create_comment(post=post, author=author, body="alex's comment")
    create_comment(post=post, author=robin, body="a reply", reply_to=own_comment)
    reporter = Profile.objects.create(
        user=User.objects.create_user(email="kai@example.com", password="a-long-enough-pw"),
        nickname="kai",
    )
    Report.objects.create(reporter=reporter, comment=own_comment)

    gated_client.force_login(author.user)
    gated_client.post("/accounts/delete/")

    assert Post.objects.filter(pk=post.pk).exists()
    assert Report.objects.count() == 1
    own_comment.refresh_from_db()
    assert own_comment.is_tombstone
    assert own_comment.author is None


# Admin (D-81) --------------------------------------------------------------------------------


@pytest.fixture
def admin_client(gated_client):
    user = User.objects.create_superuser(email="root@example.com", password="a-long-enough-pw")
    Profile.objects.create(user=user, nickname="root")
    gated_client.force_login(user)
    return gated_client


CHANGELIST = "/admin/posts/report/"


def test_the_admin_lists_a_comment_report_with_its_number_and_post(admin_client, author, comment):
    Report.objects.create(reporter=author, comment=comment, reason="Looks like spam")

    html = admin_client.get(CHANGELIST).content.decode()

    assert ">Comment<" in html
    assert f"#{comment.number}" in html
    assert "Robin&#x27;s post" in html
    assert "Looks like spam" in html


def test_a_comment_reports_link_jumps_to_the_comment(admin_client, author, post, comment):
    Report.objects.create(reporter=author, comment=comment)

    html = admin_client.get(CHANGELIST).content.decode()

    assert f'href="/posts/{post.pk}/#c-{comment.number}"' in html


def test_post_and_comment_reports_are_both_searchable_and_listed_together(
    admin_client, author, post, comment
):
    Report.objects.create(reporter=author, post=post, reason="reasonmarkerAAA")
    other_comment = create_comment(post=post, author=post.author, body="another one")
    Report.objects.create(reporter=author, comment=other_comment, reason="reasonmarkerBBB")

    html = admin_client.get(CHANGELIST).content.decode()
    search_html = admin_client.get(CHANGELIST + "?q=another").content.decode()

    assert ">Post<" in html and ">Comment<" in html
    assert "reasonmarkerAAA" in html and "reasonmarkerBBB" in html
    assert "reasonmarkerBBB" in search_html
    assert "reasonmarkerAAA" not in search_html


def test_the_delete_reported_comments_action_tombstones_the_comment(admin_client, author, comment):
    report = Report.objects.create(reporter=author, comment=comment)

    admin_client.post(
        CHANGELIST,
        {"action": "delete_reported_comments", "_selected_action": [report.pk]},
        follow=True,
    )

    comment.refresh_from_db()
    assert comment.is_tombstone
    assert Report.objects.filter(pk=report.pk).exists()  # die Meldung selbst bleibt


def test_the_delete_reported_comments_action_ignores_post_reports(admin_client, author, post):
    report = Report.objects.create(reporter=author, post=post)

    response = admin_client.post(
        CHANGELIST,
        {"action": "delete_reported_comments", "_selected_action": [report.pk]},
        follow=True,
    )

    assert b"0 comment(s) deleted" in response.content
    assert Post.objects.filter(pk=post.pk).exists()


def test_deleting_the_post_in_the_admin_removes_reports_of_its_comments(
    admin_client, author, post, comment
):
    Report.objects.create(reporter=author, comment=comment)

    admin_client.post(
        "/admin/posts/post/",
        {"action": "delete_selected", "_selected_action": [post.pk], "post": "yes"},
    )

    assert not Post.objects.filter(pk=post.pk).exists()
    assert Report.objects.count() == 0
