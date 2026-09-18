"""
Django-Admin für Freundschaften (D-71). Nur lesbar plus löschen: das
Paar liegt in kanonischer Reihenfolge und wird von Constraints
abgesichert (D-67) — Anlegen und Ändern der Profil-Felder von Hand
liefe dort nur in `IntegrityError`s. Anfragen entstehen ausschließlich
über die Views (`apps.social.friendships`).
"""

from django.contrib import admin

from .models import Friendship


@admin.register(Friendship)
class FriendshipAdmin(admin.ModelAdmin):
    list_display = ["profile_a", "profile_b", "requested_by", "status", "created_at"]
    list_filter = ["status"]
    search_fields = ["profile_a__nickname", "profile_b__nickname"]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
