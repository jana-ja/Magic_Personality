"""
Django-Admin für die Color-Info-Inhalte (D-71). Punktuelle Korrekturen
sind möglich, die Wahrheit bleiben aber die Seed-Dateien (D-28,
ARCHITECTURE.md §9): was nur hier geändert wird, geht beim nächsten
`seed_content` bzw. beim nächsten Aufsetzen verloren.
"""

from django.contrib import admin

from .models import Color, ColorCombination, CombinationTrait, Perspective, PerspectivePole, Trait


@admin.register(Color)
class ColorAdmin(admin.ModelAdmin):
    list_display = ["code", "name", "hex", "wheel_position"]


@admin.register(ColorCombination)
class ColorCombinationAdmin(admin.ModelAdmin):
    list_display = ["code", "name", "locale", "theme", "archetype"]
    list_filter = ["locale"]
    search_fields = ["code", "name"]


@admin.register(Trait)
class TraitAdmin(admin.ModelAdmin):
    list_display = ["name", "type", "locale"]
    list_filter = ["type", "locale"]
    search_fields = ["name"]


@admin.register(CombinationTrait)
class CombinationTraitAdmin(admin.ModelAdmin):
    list_display = ["combination", "trait", "leaning_toward"]
    search_fields = ["combination__code", "trait__name"]


class PerspectivePoleInline(admin.TabularInline):
    model = PerspectivePole
    extra = 0


@admin.register(Perspective)
class PerspectiveAdmin(admin.ModelAdmin):
    list_display = ["combination", "from_color", "locale"]
    list_filter = ["locale"]
    inlines = [PerspectivePoleInline]


@admin.register(PerspectivePole)
class PerspectivePoleAdmin(admin.ModelAdmin):
    list_display = ["perspective", "color", "term"]
