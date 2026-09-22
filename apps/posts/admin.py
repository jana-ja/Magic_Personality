"""
Django-Admin für Beiträge, Meldungen (Task 5.1, 5.7, 6.5, D-71, D-81) und
Kommentare (Task 6.1, D-79). Nutzerdaten sind nur lesbar: Anlegen und Ändern
läuft ausschließlich über die Views bzw. `apps.posts.comments`, die Längen,
Farbcode und Rechte prüfen. Löschen bleibt bei Beiträgen und Meldungen
möglich (D-81: die Projektinhaberin löscht gemeldete Beiträge hier), bei
Kommentaren nicht — siehe `CommentAdmin`; gemeldete Kommentare werden über
eine eigene Aktion auf `ReportAdmin` zur Hülle gemacht (Task 6.5).
"""

from django.contrib import admin
from django.urls import reverse
from django.utils import timezone
from django.utils.html import format_html

from .comments import make_tombstone
from .models import Comment, Post, Report


class ReadOnlyAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(Post)
class PostAdmin(ReadOnlyAdmin):
    list_display = ["title", "author", "colors", "created_at", "edited_at"]
    list_filter = ["colors", "visibility"]
    search_fields = ["title", "body", "author__nickname"]
    date_hierarchy = "created_at"


class ReportStatusFilter(admin.SimpleListFilter):
    """Offene oder bearbeitete Meldungen (Standard: alle)."""

    title = "status"
    parameter_name = "status"

    def lookups(self, request, model_admin):
        return [("open", "Open"), ("handled", "Handled")]

    def queryset(self, request, queryset):
        if self.value() == "open":
            return queryset.filter(handled_at__isnull=True)
        if self.value() == "handled":
            return queryset.filter(handled_at__isnull=False)
        return queryset


@admin.register(Report)
class ReportAdmin(ReadOnlyAdmin):
    """
    Die Meldungen — von Beiträgen (Task 5.7) und, seit Task 6.5, von
    Kommentaren (D-81): Ziel (Link auf die öffentliche Seite), Melderin bzw.
    Melder, Grund, Zeit und Status. Es gibt kein automatisches Ausblenden — die
    Projektinhaberin liest die Meldung und behandelt den Fall: einen Beitrag
    löscht sie unter „Posts" (verschwindet die Meldung mit ihm); einen
    Kommentar macht die Aktion `delete_reported_comments` hier zur Hülle
    (dieselbe Funktion wie beim Löschen durch die Autorin bzw. den Autor,
    `apps.posts.comments.make_tombstone`) — die Meldung bleibt danach
    bestehen, bis sie separat als bearbeitet markiert wird.
    """

    list_display = [
        "created_at",
        "target_kind",
        "target_link",
        "reporter",
        "short_reason",
        "status",
    ]
    list_filter = [ReportStatusFilter]
    list_select_related = ["reporter", "post", "comment", "comment__post"]
    search_fields = [
        "reason",
        "post__title",
        "comment__body",
        "comment__post__title",
        "reporter__nickname",
    ]
    date_hierarchy = "created_at"
    actions = ["mark_handled", "mark_open", "delete_reported_comments"]

    @admin.display(description="type")
    def target_kind(self, obj):
        return "Comment" if obj.comment_id else "Post"

    @admin.display(description="target")
    def target_link(self, obj):
        if obj.comment_id:
            url = (
                reverse("posts:detail", kwargs={"pk": obj.comment.post_id})
                + f"#c-{obj.comment.number}"
            )
            return format_html(
                '<a href="{}">#{} on “{}”</a>', url, obj.comment.number, obj.comment.post.title
            )
        url = reverse("posts:detail", kwargs={"pk": obj.post_id})
        return format_html('<a href="{}">{}</a>', url, obj.post.title)

    @admin.display(description="reason")
    def short_reason(self, obj):
        return obj.reason[:80]

    @admin.display(description="status", ordering="handled_at")
    def status(self, obj):
        return "Open" if obj.is_open else "Handled"

    @admin.action(description="Mark selected reports as handled")
    def mark_handled(self, request, queryset):
        updated = queryset.filter(handled_at__isnull=True).update(handled_at=timezone.now())
        self.message_user(request, f"{updated} report(s) marked as handled.")

    @admin.action(description="Mark selected reports as open again")
    def mark_open(self, request, queryset):
        updated = queryset.filter(handled_at__isnull=False).update(handled_at=None)
        self.message_user(request, f"{updated} report(s) reopened.")

    @admin.action(description="Delete the reported comment(s) (leaves post reports untouched)")
    def delete_reported_comments(self, request, queryset):
        comments = {report.comment_id: report.comment for report in queryset if report.comment_id}
        for comment in comments.values():
            make_tombstone(comment)
        self.message_user(request, f"{len(comments)} comment(s) deleted.")


@admin.register(Comment)
class CommentAdmin(ReadOnlyAdmin):
    """
    Nur zum Nachsehen (D-71) — anders als bei `Post`/`Report` auch **kein
    hartes Löschen über eine eigene Aktion**: Das ließe `reply_to`-Verweise
    anderer Kommentare stillschweigend ins Leere zeigen (`on_delete=SET_NULL`)
    statt als Hülle stehen zu bleiben (D-79). Deshalb fehlt `delete_selected`
    in `actions` (`get_actions()`), ersetzt durch `tombstone_selected` —
    dieselbe Funktion wie beim Löschen durch die Autorin bzw. den Autor und
    bei `ReportAdmin.delete_reported_comments` (Task 6.5).

    `has_delete_permission` bleibt bewusst die **Voreinstellung** (nicht auf
    `False` gesetzt, anders als in einer früheren Fassung dieser Klasse):
    Djangos `get_deleted_objects()` prüft beim Löschen eines *Beitrags* für
    **jedes** kaskadierte Modell dessen Löschrecht — ein pauschales `False`
    hier hätte das Löschen eines Beitrags mit Kommentaren im Admin komplett
    blockiert (gefunden über einen Test in Task 6.5, der genau das prüft).
    Ohne die eigene Löschaktion bleibt ein *einzelner* Kommentar trotzdem vor
    einem harten Löschen über die eigene Kommentarliste geschützt.
    """

    list_display = ["post", "number", "author", "short_body", "created_at", "is_tombstone"]
    list_select_related = ["post", "author"]
    search_fields = ["body", "author__nickname", "post__title"]
    date_hierarchy = "created_at"
    actions = ["tombstone_selected"]

    def get_actions(self, request):
        actions = super().get_actions(request)
        actions.pop("delete_selected", None)
        return actions

    @admin.display(description="body")
    def short_body(self, obj):
        return obj.body[:80]

    @admin.display(boolean=True, description="tombstone")
    def is_tombstone(self, obj):
        return obj.is_tombstone

    @admin.action(description="Delete the selected comment(s)")
    def tombstone_selected(self, request, queryset):
        count = 0
        for comment in queryset:
            make_tombstone(comment)
            count += 1
        self.message_user(request, f"{count} comment(s) deleted.")
