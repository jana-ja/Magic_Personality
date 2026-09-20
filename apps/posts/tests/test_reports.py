"""
Tests für das Melden von Beiträgen (Task 5.7, FR-B10, FR-B11, D-81).
"""

import pytest
from django.conf import settings
from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.accounts.models import Profile, User
from apps.posts.models import Post, PostQuerySet, Report

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
def member(gated_client, author):
    gated_client.force_login(author.user)
    return gated_client


def _url(post):
    return f"/posts/{post.pk}/report/"


# Zugriff ------------------------------


def test_reporting_needs_the_gate(client, post):
    response = client.get(_url(post))

    assert response.status_code == 302
    assert response.url.startswith("/gate/")


def test_guests_are_sent_to_the_login(gated_client, post):
    for response in (gated_client.get(_url(post)), gated_client.post(_url(post), {"reason": "x"})):
        assert response.status_code == 302
        assert response.url.startswith("/accounts/login/")
    assert Report.objects.count() == 0


def test_an_unknown_post_is_404(member):
    assert member.get("/posts/999999/report/").status_code == 404
    assert member.post("/posts/999999/report/", {}).status_code == 404


def test_a_post_that_is_not_visible_cannot_be_reported(member, post, monkeypatch):
    monkeypatch.setattr(PostQuerySet, "visible_to", lambda self, profile: self.none())

    assert member.get(_url(post)).status_code == 404
    assert member.post(_url(post), {}).status_code == 404
    assert Report.objects.count() == 0


def test_only_get_and_post_are_allowed(member, post):
    assert member.put(_url(post)).status_code == 405


# Der eigene Beitrag ------------------------------


def test_your_own_post_cannot_be_reported(member, author):
    own = Post.objects.create(author=author, title="Mine", body="b")

    got = member.get(_url(own))
    posted = member.post(_url(own), {"reason": "spam"})

    for response in (got, posted):
        assert response.status_code == 302
        assert response.url == f"/posts/{own.pk}/"
    assert Report.objects.count() == 0


def test_the_post_page_offers_reporting_only_for_other_peoples_posts(member, author, post):
    own = Post.objects.create(author=author, title="Mine", body="b")

    foreign_page = member.get(f"/posts/{post.pk}/").content.decode()
    own_page = member.get(f"/posts/{own.pk}/").content.decode()

    assert f'href="{_url(post)}"' in foreign_page
    assert f'hx-get="{_url(post)}"' in foreign_page
    assert 'id="report"' in foreign_page
    assert "/report/" not in own_page and 'id="report"' not in own_page


# Formular ------------------------------


def test_the_report_page_shows_the_form_without_javascript(member, post):
    html = member.get(_url(post)).content.decode()

    assert "Report post" in html
    assert "Robin&#x27;s post" in html or "Robin's post" in html
    assert 'name="reason"' in html
    assert "Nothing happens automatically." in html
    assert f'action="{_url(post)}"' in html


def test_htmx_gets_only_the_form_fragment(member, post):
    html = member.get(_url(post), **HTMX).content.decode()

    assert "<html" not in html
    assert 'name="reason"' in html


# Melden ------------------------------


def test_a_report_is_stored_with_reporter_post_and_reason(member, author, post):
    response = member.post(_url(post), {"reason": "  This is spam.  "})

    report = Report.objects.get()
    assert response.status_code == 302
    assert response.url == f"{_url(post)}thanks/"
    assert (report.reporter, report.post, report.reason) == (author, post, "This is spam.")
    assert report.handled_at is None and report.is_open


def test_the_reason_is_optional(member, post):
    member.post(_url(post), {"reason": ""})
    member.post(_url(post), {})  # zweite Meldung derselben Person: schon gemeldet

    assert Report.objects.count() == 1
    assert Report.objects.get().reason == ""


def test_windows_line_endings_are_stored_as_line_feeds(member, post):
    member.post(_url(post), {"reason": "line one\r\nline two"})

    assert Report.objects.get().reason == "line one\nline two"


def test_a_reason_of_500_characters_is_fine_and_501_is_rejected(member, post, robin):
    other = Post.objects.create(author=robin, title="Other", body="b")

    ok = member.post(_url(post), {"reason": "x" * 500})
    too_long = member.post(_url(other), {"reason": "x" * 501})

    assert ok.status_code == 302
    assert too_long.status_code == 200
    assert Report.objects.count() == 1
    assert Report.objects.get().post == post


def test_the_thanks_page_confirms_after_a_report(member, post):
    member.post(_url(post), {"reason": "x"})

    html = member.get(f"{_url(post)}thanks/").content.decode()

    assert "Thank you, we will look at it." in html


def test_the_thanks_page_without_a_report_leads_back_to_the_form(member, post):
    response = member.get(f"{_url(post)}thanks/")

    assert response.status_code == 302
    assert response.url == _url(post)


def test_htmx_returns_only_the_thanks_fragment(member, post):
    response = member.post(_url(post), {"reason": "x"}, **HTMX)

    html = response.content.decode()
    assert response.status_code == 200
    assert "<html" not in html
    assert "Thank you, we will look at it." in html
    assert Report.objects.count() == 1


def test_an_invalid_htmx_report_shows_the_form_again_with_the_error(member, post):
    response = member.post(_url(post), {"reason": "x" * 501}, **HTMX)

    html = response.content.decode()
    assert "<html" not in html
    assert 'name="reason"' in html
    assert "Ensure this value has at most 500 characters" in html
    assert Report.objects.count() == 0


def test_a_rejected_reason_is_shown_again_escaped(member, post):
    html = member.post(_url(post), {"reason": "<script>alert(1)</script>" * 30}).content.decode()

    assert "<script>alert(1)</script>" not in html


# Einmal je Person und Beitrag ------------------------------


def test_reporting_twice_creates_no_second_report(member, post):
    member.post(_url(post), {"reason": "first"})

    again = member.post(_url(post), {"reason": "second"})

    assert again.status_code == 200
    assert "You have already reported this post." in again.content.decode()
    assert Report.objects.get().reason == "first"


def test_the_form_is_replaced_by_a_note_once_reported(member, post):
    member.post(_url(post), {"reason": "x"})

    page = member.get(_url(post)).content.decode()
    detail = member.get(f"/posts/{post.pk}/").content.decode()

    assert "You have already reported this post." in page and 'name="reason"' not in page
    assert "You have reported this post." in detail
    assert f'href="{_url(post)}"' not in detail


def test_the_database_allows_one_report_per_person_and_post(author, post):
    Report.objects.create(reporter=author, post=post)

    with pytest.raises(IntegrityError), transaction.atomic():
        Report.objects.create(reporter=author, post=post)


def test_different_people_can_report_the_same_post(member, make_profile, post):
    member.post(_url(post), {"reason": "one"})
    member.force_login(make_profile("sam").user)
    member.post(_url(post), {"reason": "two"})

    assert Report.objects.count() == 2


def test_one_person_can_report_several_posts(member, robin, post):
    other = Post.objects.create(author=robin, title="Other", body="b")

    member.post(_url(post), {})
    member.post(_url(other), {})

    assert Report.objects.count() == 2


# Grenze (FR-B11) ------------------------------


def _fill_up_the_limit(reporter, robin):
    for number in range(settings.REPORT_RATE_LIMIT_MAX_REPORTS):
        target = Post.objects.create(author=robin, title=f"P{number}", body="b")
        Report.objects.create(reporter=reporter, post=target)


def test_beyond_the_limit_no_report_is_created_and_the_reason_is_shown(member, author, robin, post):
    _fill_up_the_limit(author, robin)

    response = member.post(_url(post), {"reason": "one too many"})

    assert response.status_code == 429
    assert "reporting too fast" in response.content.decode()
    assert "one too many" in response.content.decode()
    assert Report.objects.count() == settings.REPORT_RATE_LIMIT_MAX_REPORTS


def test_the_limit_message_is_visible_with_htmx_too(member, author, robin, post):
    _fill_up_the_limit(author, robin)

    response = member.post(_url(post), {"reason": "x"}, **HTMX)

    assert response.status_code == 200
    assert "reporting too fast" in response.content.decode()
    assert Report.objects.filter(post=post).count() == 0


def test_old_reports_and_other_peoples_reports_do_not_count(
    member, author, robin, post, make_profile
):
    _fill_up_the_limit(make_profile("sam"), robin)
    assert member.post(_url(post), {}).status_code == 302

    old = timezone.now() - timezone.timedelta(
        seconds=settings.REPORT_RATE_LIMIT_WINDOW_SECONDS + 60
    )
    _fill_up_the_limit(author, robin)
    Report.objects.filter(reporter=author).update(created_at=old)
    another = Post.objects.create(author=robin, title="Another", body="b")

    assert member.post(_url(another), {}).status_code == 302


# Aufräumen (D-81) ------------------------------


def test_a_report_disappears_with_the_reported_post(author, post):
    Report.objects.create(reporter=author, post=post)

    post.delete()

    assert Report.objects.count() == 0


def test_a_report_disappears_with_the_reporters_account(author, post):
    Report.objects.create(reporter=author, post=post)

    author.user.delete()

    assert Report.objects.count() == 0
    assert Post.objects.filter(pk=post.pk).exists()


def test_deleting_the_authors_account_removes_the_reports_about_their_posts(author, robin, post):
    Report.objects.create(reporter=author, post=post)

    robin.user.delete()

    assert Report.objects.count() == 0


# Admin (D-81) ------------------------------


@pytest.fixture
def admin_client(gated_client):
    user = User.objects.create_superuser(email="root@example.com", password="a-long-enough-pw")
    Profile.objects.create(user=user, nickname="root")
    gated_client.force_login(user)
    return gated_client


CHANGELIST = "/admin/posts/report/"


def test_the_admin_lists_reports_with_post_reporter_and_reason(admin_client, author, post):
    Report.objects.create(reporter=author, post=post, reason="Looks like spam")

    html = admin_client.get(CHANGELIST).content.decode()

    assert f'<a href="/posts/{post.pk}/">Robin&#x27;s post</a>' in html
    assert "alex" in html and "Looks like spam" in html and "Open" in html


def test_the_admin_escapes_the_reason(admin_client, author, post):
    Report.objects.create(reporter=author, post=post, reason="<script>alert(1)</script>")

    html = admin_client.get(CHANGELIST).content.decode()

    assert "<script>alert(1)</script>" not in html


def test_the_admin_filters_open_and_handled_reports(admin_client, author, robin, post):
    other = Post.objects.create(author=robin, title="Handled one", body="b")
    Report.objects.create(reporter=author, post=post)
    Report.objects.create(reporter=author, post=other, handled_at=timezone.now())

    open_html = admin_client.get(CHANGELIST + "?status=open").content.decode()
    handled_html = admin_client.get(CHANGELIST + "?status=handled").content.decode()

    assert "Robin&#x27;s post" in open_html and "Handled one" not in open_html
    assert "Handled one" in handled_html and "Robin&#x27;s post" not in handled_html


def test_the_admin_can_mark_reports_as_handled_and_reopen_them(admin_client, author, post):
    report = Report.objects.create(reporter=author, post=post)

    admin_client.post(
        CHANGELIST, {"action": "mark_handled", "_selected_action": [report.pk]}, follow=True
    )
    report.refresh_from_db()
    assert report.handled_at is not None

    admin_client.post(
        CHANGELIST, {"action": "mark_open", "_selected_action": [report.pk]}, follow=True
    )
    report.refresh_from_db()
    assert report.handled_at is None


def test_the_admin_cannot_add_or_change_a_report(admin_client, author, post):
    report = Report.objects.create(reporter=author, post=post)

    assert admin_client.get(CHANGELIST + "add/").status_code == 403
    assert admin_client.post(f"{CHANGELIST}{report.pk}/change/", {"reason": "x"}).status_code == 403


def test_deleting_the_post_in_the_admin_removes_its_reports(admin_client, author, post):
    Report.objects.create(reporter=author, post=post)

    admin_client.post(
        "/admin/posts/post/",
        {"action": "delete_selected", "_selected_action": [post.pk], "post": "yes"},
    )

    assert not Post.objects.filter(pk=post.pk).exists()
    assert Report.objects.count() == 0
