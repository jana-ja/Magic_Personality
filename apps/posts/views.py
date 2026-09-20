"""
Views der Posts-App: Beitrag schreiben, bearbeiten, löschen (Task 5.3,
FR-B1 bis FR-B4, FR-B11) und die Beitragsseite (Task 5.4, FR-B5). Die Listen
(Task 5.5, 5.6) kommen mit den eigenen Tasks.

Jeder View verlangt eine Anmeldung (FR-B8) und liest Beiträge nur über
`Post.objects.visible_to()` (FR-B9).
"""

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext as _
from django.views.decorators.http import require_http_methods

from apps.colors import selection
from apps.colors.field import color_field_context

from . import combinations, limits
from .decorators import author_only, current_profile
from .forms import PostForm
from .markdown import render_markdown
from .models import Post


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
            profile.posts.all(),
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
        # Task 5.5 leitet stattdessen auf den Tab „Posts" des Profils.
        return redirect(profile)
    return render(request, "posts/post_confirm_delete.html", {"post": post})


@login_required
@require_http_methods(["GET"])
def post_detail(request, pk):
    """
    FR-B5: die Seite eines Beitrags — Autorenkarte, Farbkombination (Link auf
    die Color Infos, oder „General"), Datum, „edited" und der gerenderte
    Text; die Autorin bzw. der Autor sieht „Edit" und „Delete". Unbekannte
    und nicht sichtbare Beiträge sind 404 (`visible_to`). Kommentare kommen
    mit v1.4.
    """
    profile = current_profile(request)
    post = get_object_or_404(
        Post.objects.visible_to(profile)
        .select_related("author")
        .prefetch_related("author__color_assignments__combination"),
        pk=pk,
    )
    combination = None
    if post.colors:
        combination = {
            "label": combinations.combination_labels([post.colors])[post.colors],
            "url": combinations.combination_url(post.colors),
        }
    return render(
        request,
        "posts/post_detail.html",
        {"post": post, "combination": combination, "is_author": post.author_id == profile.pk},
    )
