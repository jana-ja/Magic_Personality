"""
Django-Admin für Beiträge und Meldungen (Task 5.1, 5.7, D-71, D-81). Nutzerdaten
sind nur lesbar, löschen bleibt möglich (D-81: die Projektinhaberin löscht
gemeldete Beiträge hier): Anlegen und Ändern läuft ausschließlich über die
Views, die Längen, Farbcode und Rechte prüfen.
"""

from django.contrib import admin
from django.urls import reverse
from django.utils import timezone
from django.utils.html import format_html

from .models import Post, Report


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
    Die Meldungen (D-81): Beitrag (Link auf die öffentliche Seite), Melderin bzw.
    Melder, Grund, Zeit und Status. Es gibt kein automatisches Ausblenden — die
    Projektinhaberin liest die Meldung, prüft den Beitrag und löscht ihn bei
    Bedarf unter „Posts"; danach verschwindet die Meldung mit ihm.
    """

    list_display = ["created_at", "post_link", "reporter", "short_reason", "status"]
    list_filter = [ReportStatusFilter]
    list_select_related = ["reporter", "post"]
    search_fields = ["reason", "post__title", "reporter__nickname"]
    date_hierarchy = "created_at"
    actions = ["mark_handled", "mark_open"]

    @admin.display(description="post", ordering="post__title")
    def post_link(self, obj):
        return format_html(
            '<a href="{}">{}</a>',
            reverse("posts:detail", kwargs={"pk": obj.post_id}),
            obj.post.title,
        )

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
