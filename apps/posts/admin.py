"""
Django-Admin für Beiträge (Task 5.1, D-71). Nutzerdaten sind nur lesbar,
löschen bleibt möglich (D-81: die Projektinhaberin löscht gemeldete
Beiträge hier): Anlegen und Ändern läuft ausschließlich über die Views,
die Längen, Farbcode und Rechte prüfen.
"""

from django.contrib import admin

from .models import Post


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ["title", "author", "colors", "created_at", "edited_at"]
    list_filter = ["colors", "visibility"]
    search_fields = ["title", "body", "author__nickname"]
    date_hierarchy = "created_at"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
