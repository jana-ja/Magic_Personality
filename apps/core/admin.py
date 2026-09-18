"""Django-Admin für die Rate-Limit-Protokolle (D-71) — nur lesbar."""

from django.contrib import admin

from .models import GateAttempt, RegistrationAttempt


class AttemptAdmin(admin.ModelAdmin):
    list_display = ["ip_address", "created_at"]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


admin.site.register(GateAttempt, AttemptAdmin)
admin.site.register(RegistrationAttempt, AttemptAdmin)
