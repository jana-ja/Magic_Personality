"""
Views der Posts-App: Beitrag schreiben, bearbeiten, löschen (Task 5.3,
FR-B1 bis FR-B4, FR-B11), die Beitragsseite (Task 5.4, FR-B5), Kommentare
darauf (Task 6.2, FR-B13, FR-B15, FR-B18), Kommentare löschen (Task 6.3,
FR-B16), Beiträge melden (Task 5.7, FR-B10) und Kommentare melden
(Task 6.5, FR-B18). Die Listen (Task 5.5, 5.6) kommen mit den eigenen
Tasks.

Jeder View verlangt eine Anmeldung (FR-B8) und liest Beiträge nur über
`Post.objects.visible_to()` (FR-B9).
"""

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views.decorators.http import require_http_methods

from apps.colors import selection
from apps.colors.field import color_field_context

from . import combinations, limits
from .comments import create_comment, make_tombstone
from .decorators import author_only, current_profile
from .forms import CommentForm, PostForm, ReportForm
from .markdown import render_markdown
from .models import Comment, Post, Report


def _prefilled_colors(request):
    """`?colors=wg` (Link „Write a post about this", Task 5.6) belegt die Farben
    vor; ungültige Angaben werden still ignoriert."""
    colors = selection.parse_url_code(request.GET.get("colors", ""))
    return sorted(colors) if colors else []


def _editor_context(form, *, post=None, preview=None):
    selected = set(form["colors"].value() or [])
    return {
        "form": form,
        "post": post,
        "preview": preview,
        **color_field_context(selected),
    }


def _is_htmx(request):
    return request.headers.get("HX-Request") == "true"


def _editor(request, *, profile, post=None):
    """
    Gemeinsamer Ablauf von „neu" und „bearbeiten": GET zeigt das Formular,
    `action=preview` zeigt den Text gerendert (ohne zu speichern, ohne die
    Grenze zu berühren, ohne zu prüfen — auch ein halb fertiger Text soll sich
    ansehen lassen), sonst wird gespeichert.

    Die Vorschau ist derselbe Renderer wie die Anzeige (D-80). Mit HTMX
    kommt nur der Vorschau-Baustein zurück, ohne JavaScript die ganze Seite
    mit dem Formular — so funktioniert sie auch dort.
    """
    if request.method == "POST":
        if request.POST.get("action") == "preview":
            body = request.POST.get("body", "").replace("\r\n", "\n").replace("\r", "\n")
            preview = {
                "title": request.POST.get("title", "").strip(),
                "html": render_markdown(body),
            }
            if _is_htmx(request):
                return render(request, "posts/_preview.html", {"preview": preview})
            form = PostForm(
                initial={
                    "title": request.POST.get("title", ""),
                    "body": request.POST.get("body", ""),
                    "colors": request.POST.getlist("colors"),
                },
                post=post,
            )
            return render(
                request, "posts/post_form.html", _editor_context(form, post=post, preview=preview)
            )

        form = PostForm(request.POST, post=post)
        if post is None and limits.is_limited(
            Post.objects.visible_to(profile).filter(author=profile),
            max_count=settings.POST_RATE_LIMIT_MAX_POSTS,
            window_seconds=settings.POST_RATE_LIMIT_WINDOW_SECONDS,
        ):
            form.add_error(None, _("You are posting too fast. Please try again later."))
            return render(request, "posts/post_form.html", _editor_context(form), status=429)
        if form.is_valid():
            saved = form.save(author=profile)
            return redirect("posts:detail", pk=saved.pk)
        return render(request, "posts/post_form.html", _editor_context(form, post=post))

    if post is None:
        form = PostForm(initial={"colors": _prefilled_colors(request)})
    else:
        form = PostForm(post=post)
    return render(request, "posts/post_form.html", _editor_context(form, post=post))


@login_required
@require_http_methods(["GET", "POST"])
def new_post(request):
    """FR-B1, FR-B2: neuen Beitrag schreiben; Grenze FR-B11 (30 je Person und Stunde)."""
    return _editor(request, profile=current_profile(request))


@author_only
@require_http_methods(["GET", "POST"])
def edit_post(request, post, profile):
    """FR-B4: nur die Autorin bzw. der Autor; `edited_at` nur bei tatsächlicher Änderung."""
    return _editor(request, profile=profile, post=post)


@author_only
@require_http_methods(["GET", "POST"])
def delete_post(request, post, profile):
    """
    FR-B4: GET zeigt nur die Bestätigung, erst ein eigenes POST löscht
    (wie beim Account, FR-U8). Kommentare, Pins und Meldungen hängen per
    Kaskade am Beitrag und verschwinden mit ihm.
    """
    if request.method == "POST":
        post.delete()
        return redirect("social:profile_posts", nickname=profile.nickname)
    return render(request, "posts/post_confirm_delete.html", {"post": post})


def _post_extras(post, profile):
    """Der Teil des Beitragsseiten-Kontexts, der nichts mit Kommentaren zu tun
    hat (Task 5.4): Farbkombination, Autorenrechte, Meldestatus."""
    combination = None
    if post.colors:
        combination = {
            "label": combinations.combination_labels([post.colors])[post.colors],
            "url": combinations.combination_url(post.colors),
        }
    is_author = post.author_id == profile.pk
    return {
        "combination": combination,
        "is_author": is_author,
        # Nur fremde Beiträge lassen sich melden (FR-B10).
        "already_reported": not is_author
        and Report.objects.filter(reporter=profile, post=post).exists(),
    }


def _reply_number(raw):
    """Eine Nummer aus `?reply=` oder dem `reply_to`-Feld des Formulars —
    leer oder keine (positive) Zahl wird zu `None`, ohne Fehler (wie bei
    `?colors=`, Task 5.6)."""
    return int(raw) if raw and raw.isdigit() else None


def _find_replyable(post, number):
    """Der Kommentar `#number` dieses Beitrags, wenn er existiert und keine
    Hülle ist (FR-B15) — sonst `None`. Eine veraltete oder erfundene Nummer
    blockiert niemanden, sie wird einfach zu „kein Bezug"."""
    if number is None:
        return None
    return Comment.objects.filter(post=post, number=number, deleted_at__isnull=True).first()


def _comments_context(post, *, viewer_id, reply_number=None, comment_form=None):
    """
    Kommentarliste und -formular für die Beitragsseite und den Baustein
    `#comments` (Task 6.2). `comment_form=None` erzeugt ein leeres Formular,
    mit `reply_to` vorbelegt, wenn `reply_number` einen echten Kommentar
    trifft — sonst ein übergebenes (gebundenes, ggf. fehlerhaftes)
    Formular unverändert weiterreichen. `viewer_id` reicht das Template
    durch, um „Delete" nur am eigenen Kommentar zu zeigen (Task 6.3,
    FR-B16) — ein bloßer Vergleich, kein zweiter Zugriffsschutz: den trifft
    ausschließlich der View `delete_comment` selbst. Dasselbe gilt für
    `already_reported_comment_ids` (Task 6.5, FR-B18): eine Abfrage für die
    ganze Liste, nicht eine je Kommentar.
    """
    replying_to = _find_replyable(post, reply_number)
    if comment_form is None:
        initial = {"reply_to": replying_to.number} if replying_to else None
        comment_form = CommentForm(initial=initial)
    comments = list(
        Comment.objects.for_post(post)
        # "author": die Autorenkarte je Kommentar. "reply_to": der Verweis
        # "↪ #m" braucht dessen Nummer — sonst eine Abfrage je Antwort.
        .select_related("author", "reply_to")
        .prefetch_related("author__color_assignments__combination")
    )
    already_reported_comment_ids = set(
        Report.objects.filter(
            reporter_id=viewer_id, comment_id__in=[comment.pk for comment in comments]
        ).values_list("comment_id", flat=True)
    )
    return {
        "post": post,
        "comments": comments,
        "comment_form": comment_form,
        "replying_to": replying_to,
        "viewer_id": viewer_id,
        "already_reported_comment_ids": already_reported_comment_ids,
    }


@login_required
@require_http_methods(["GET"])
def post_detail(request, pk):
    """
    FR-B5: die Seite eines Beitrags — Autorenkarte, Farbkombination (Link auf
    die Color Infos, oder „General"), Datum, „edited" und der gerenderte
    Text; die Autorin bzw. der Autor sieht „Edit" und „Delete". Darunter die
    Kommentare (Task 6.2). Unbekannte und nicht sichtbare Beiträge sind 404
    (`visible_to`).
    """
    profile = current_profile(request)
    post = get_object_or_404(
        Post.objects.visible_to(profile)
        .select_related("author")
        .prefetch_related("author__color_assignments__combination"),
        pk=pk,
    )
    reply_number = _reply_number(request.GET.get("reply", ""))
    return render(
        request,
        "posts/post_detail.html",
        {
            **_post_extras(post, profile),
            **_comments_context(post, viewer_id=profile.pk, reply_number=reply_number),
        },
    )


@login_required
@require_http_methods(["POST"])
def add_comment(request, pk):
    """
    FR-B13, FR-B15: einen Kommentar anlegen. `Post.objects.visible_to()`
    entscheidet wie überall, ob der Beitrag überhaupt erreichbar ist
    (FR-B8/FR-B9) — dieselbe Prüfung sitzt noch einmal in
    `apps.posts.comments.create_comment()` (Task 6.1). Die Grenze (FR-B18)
    steht hier statt in einem Decorator, damit ihre Meldung auch bei HTMX
    (kein 4xx-Austausch) sichtbar ist — wie bei Beiträgen (5.3) und
    Meldungen (5.7).

    Mit HTMX kommt nur der Baustein `#comments` zurück, der neue Kommentar
    erscheint ohne Seitenwechsel; ohne JavaScript ein POST mit Weiterleitung
    auf den Anker `#c-<nummer>` des neuen Kommentars (FR-B14).
    """
    profile = current_profile(request)
    post = get_object_or_404(Post.objects.visible_to(profile), pk=pk)

    form = CommentForm(request.POST)
    status = 200
    if limits.is_limited(
        Comment.objects.filter(author=profile),
        max_count=settings.COMMENT_RATE_LIMIT_MAX_COMMENTS,
        window_seconds=settings.COMMENT_RATE_LIMIT_WINDOW_SECONDS,
    ):
        form.add_error(None, _("You are commenting too fast. Please try again later."))
        status = 200 if _is_htmx(request) else 429
    elif form.is_valid():
        reply_to = _find_replyable(post, form.cleaned_data["reply_to"])
        comment = create_comment(
            post=post, author=profile, body=form.cleaned_data["body"], reply_to=reply_to
        )
        if _is_htmx(request):
            context = _comments_context(post, viewer_id=profile.pk)
            return render(request, "posts/_comments_section.html", context)
        anchor = reverse("posts:detail", kwargs={"pk": post.pk}) + f"#c-{comment.number}"
        return redirect(anchor)

    context = _comments_context(
        post,
        viewer_id=profile.pk,
        reply_number=_reply_number(request.POST.get("reply_to", "")),
        comment_form=form,
    )
    if _is_htmx(request):
        return render(request, "posts/_comments_section.html", context, status=status)
    return render(
        request, "posts/post_detail.html", {**_post_extras(post, profile), **context}, status=status
    )


@login_required
@require_http_methods(["GET", "POST"])
def delete_comment(request, post_pk, pk):
    """
    FR-B16, D-79: Die Autorin bzw. der Autor löscht den eigenen Kommentar —
    er wird zur Hülle (`apps.posts.comments.make_tombstone()`), nicht
    wirklich entfernt: Nummer und „↪ #m"-Verweise anderer Kommentare bleiben
    stabil. GET zeigt nur die Bestätigung, erst ein eigenes POST löscht
    (wie bei Beiträgen, FR-B4).

    Jede andere Person — auch die des Beitrags, falls verschieden — landet
    ohne Änderung auf der Beitragsseite; eine bereits gelöschte Zeile hat
    keinen Autor mehr (`author=None`) und fällt in denselben Fall, ganz ohne
    eigene Prüfung auf „schon eine Hülle".
    """
    profile = current_profile(request)
    post = get_object_or_404(Post.objects.visible_to(profile), pk=post_pk)
    comment = get_object_or_404(Comment, pk=pk, post=post)
    if comment.author_id != profile.pk:
        return redirect("posts:detail", pk=post.pk)

    if request.method == "POST":
        make_tombstone(comment)
        return redirect("posts:detail", pk=post.pk)
    return render(request, "posts/comment_confirm_delete.html", {"post": post, "comment": comment})


def _process_report(request, profile, report_kwargs):
    """
    Rate-Limit, Formular und Anlegen einer Meldung — gemeinsam für Beitrag
    (Task 5.7) und Kommentar (Task 6.5, FR-B10, FR-B18, D-81): **eine**
    Grenze für beide, `profile.reports.all()` unterscheidet nicht nach Ziel.
    `report_kwargs` ist `{"post": post}` oder `{"comment": comment}` — genau
    das eine Feld, das `Report` gesetzt haben will (D-81-Constraint).

    Gibt `(outcome, form, status)` zurück, `outcome` eines von `"sent"`,
    `"already"` (zwei gleichzeitige Absendungen — die Datenbank hat den
    Unique-Constraint schon durchgesetzt, das hier fängt nur die Ausnahme)
    oder `"form"`. Die Antwort selbst (Weiterleitung, ganze Seite oder
    HTMX-Baustein) baut die Aufruferin: Adressen und Vorlagen unterscheiden
    sich zwischen Beitrag und Kommentar, dieser Teil nicht.
    """
    if request.method != "POST":
        return "form", ReportForm(), 200

    form = ReportForm(request.POST)
    if limits.is_limited(
        profile.reports.all(),
        max_count=settings.REPORT_RATE_LIMIT_MAX_REPORTS,
        window_seconds=settings.REPORT_RATE_LIMIT_WINDOW_SECONDS,
    ):
        form.add_error(None, _("You are reporting too fast. Please try again later."))
        return "form", form, 200 if _is_htmx(request) else 429
    if not form.is_valid():
        return "form", form, 200

    try:
        with transaction.atomic():
            Report.objects.create(
                reporter=profile, reason=form.cleaned_data["reason"], **report_kwargs
            )
    except IntegrityError:
        return "already", None, 200
    return "sent", None, 200


def _report_response(request, post, **context):
    """Vollständige Seite, oder nur der Baustein bei HTMX (`#report` auf der Beitragsseite)."""
    template = "posts/_report_body.html" if _is_htmx(request) else "posts/report_form.html"
    status = context.pop("status", 200)
    return render(request, template, {"post": post, **context}, status=status)


@login_required
@require_http_methods(["GET", "POST"])
def report_post(request, pk):
    """
    FR-B10, D-81: einen fremden Beitrag melden, einmal je Person, mit
    optionalem Grund. Der eigene Beitrag lässt sich nicht melden (302 zurück
    auf die Beitragsseite, ohne etwas anzulegen). Die Meldung sieht nur die
    Projektinhaberin im Admin.

    Wie beim Feedback (D-75): mit HTMX kommt nur der Baustein für den Bereich
    `#report` zurück, ohne JavaScript eine eigene Seite und nach dem Senden
    eine Weiterleitung auf die Dankeseite.
    """
    profile = current_profile(request)
    post = get_object_or_404(Post.objects.visible_to(profile), pk=pk)
    if post.author_id == profile.pk:
        return redirect("posts:detail", pk=post.pk)
    if Report.objects.filter(reporter=profile, post=post).exists():
        return _report_response(request, post, already=True)

    outcome, payload, status = _process_report(request, profile, {"post": post})
    if outcome == "sent":
        if _is_htmx(request):
            return _report_response(request, post, sent=True)
        return redirect("posts:report_thanks", pk=post.pk)
    if outcome == "already":
        return _report_response(request, post, already=True)
    return _report_response(request, post, form=payload, status=status)


@login_required
@require_http_methods(["GET"])
def report_thanks(request, pk):
    """Dankeseite nach dem Melden ohne JavaScript; ohne eigene Meldung zurück zum Formular."""
    profile = current_profile(request)
    post = get_object_or_404(Post.objects.visible_to(profile), pk=pk)
    if not Report.objects.filter(reporter=profile, post=post).exists():
        return redirect("posts:report", pk=post.pk)
    return _report_response(request, post, sent=True)


def _comment_report_response(request, post, comment, **context):
    """Vollständige Seite, oder nur der Baustein bei HTMX (`#report-comment-<pk>` auf der
    Beitragsseite, Task 6.5) — Gegenstück zu `_report_response()` für Kommentare."""
    template = (
        "posts/_comment_report_body.html" if _is_htmx(request) else "posts/comment_report_form.html"
    )
    status = context.pop("status", 200)
    return render(request, template, {"post": post, "comment": comment, **context}, status=status)


@login_required
@require_http_methods(["GET", "POST"])
def report_comment(request, post_pk, pk):
    """
    FR-B18, D-81: einen fremden Kommentar melden — sonst wie `report_post`,
    mit derselben Grenze (`_process_report()`, gemeinsam gezählt). Der
    eigene Kommentar lässt sich nicht melden, eine Hülle auch nicht (sie hat
    ohnehin keinen Autor mehr und nichts mehr zu melden).
    """
    profile = current_profile(request)
    post = get_object_or_404(Post.objects.visible_to(profile), pk=post_pk)
    comment = get_object_or_404(Comment, pk=pk, post=post)
    if comment.is_tombstone or comment.author_id == profile.pk:
        return redirect("posts:detail", pk=post.pk)
    if Report.objects.filter(reporter=profile, comment=comment).exists():
        return _comment_report_response(request, post, comment, already=True)

    outcome, payload, status = _process_report(request, profile, {"comment": comment})
    if outcome == "sent":
        if _is_htmx(request):
            return _comment_report_response(request, post, comment, sent=True)
        return redirect("posts:comment_report_thanks", post_pk=post.pk, pk=comment.pk)
    if outcome == "already":
        return _comment_report_response(request, post, comment, already=True)
    return _comment_report_response(request, post, comment, form=payload, status=status)


@login_required
@require_http_methods(["GET"])
def comment_report_thanks(request, post_pk, pk):
    """Dankeseite nach dem Melden eines Kommentars ohne JavaScript."""
    profile = current_profile(request)
    post = get_object_or_404(Post.objects.visible_to(profile), pk=post_pk)
    comment = get_object_or_404(Comment, pk=pk, post=post)
    if not Report.objects.filter(reporter=profile, comment=comment).exists():
        return redirect("posts:comment_report", post_pk=post.pk, pk=comment.pk)
    return _comment_report_response(request, post, comment, sent=True)
