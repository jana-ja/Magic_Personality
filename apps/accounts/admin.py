"""
Django-Admin für Accounts und Profile (D-71).

Werkzeug zum Nachschauen und für punktuelle Korrekturen (D-28) — nicht
Teil der Nutzeroberfläche. Das Admin liegt wie alles andere hinter der
Zugangssperre (FR-A1) und braucht zusätzlich einen Account mit
`is_staff`.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import ColorAssignment, Profile, User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    """Djangos `UserAdmin` erwartet ein `username`-Feld (D-26: es gibt
    keins, E-Mail ist das Anmeldefeld) — Felder und Sortierung deshalb
    ausdrücklich auf `email` umgestellt. Über die Passwort-Änderungsseite
    im Admin lässt sich auch ein vergessenes Passwort zurücksetzen (R-1)."""

    ordering = ["email"]
    list_display = ["email", "is_staff", "is_superuser", "is_active", "date_joined"]
    list_filter = ["is_staff", "is_superuser", "is_active"]
    search_fields = ["email"]
    fieldsets = [
        (None, {"fields": ["email", "password"]}),
        ("Permissions", {"fields": ["is_active", "is_staff", "is_superuser"]}),
        ("Dates", {"fields": ["last_login", "date_joined"]}),
    ]
    add_fieldsets = [
        (None, {"classes": ["wide"], "fields": ["email", "password1", "password2"]}),
    ]
    # Gruppen und Einzelrechte kennt v1 nicht (PermissionsMixin nur als
    # Vorbereitung für Kuratoren, ARCHITECTURE.md §6.1).
    filter_horizontal = []


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ["nickname", "user", "created_at"]
    search_fields = ["nickname", "user__email"]


@admin.register(ColorAssignment)
class ColorAssignmentAdmin(admin.ModelAdmin):
    """`source` und `test_result` zusammen in der Liste: genau die
    Kombination, an der sich Zuordnungen ohne Testreferenz erkennen
    lassen (`SELF_TEST` ohne Ergebnis, FR-P8)."""

    list_display = ["profile", "combination", "source", "test_result", "created_at"]
    list_filter = ["source"]
    search_fields = ["profile__nickname"]
