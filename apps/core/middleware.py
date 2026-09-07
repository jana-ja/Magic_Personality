"""
Zugangssperre als Middleware (Task 0.5, D-09).

Blockiert die gesamte Anwendung, solange kein gültiges Gate-Cookie
vorliegt — bewusst auch /admin/ und jeden nicht existierenden Pfad
(FR-A1: "keine Seite und kein API-Endpunkt außer der Code-Eingabe").
Ausgenommen sind nur die Pfade aus apps.core.gate.is_exempt_path.

Setzt außerdem den X-Robots-Tag-Header auf jede Antwort (FR-A4) —
unabhängig davon, ob die Anfrage durchgelassen oder umgeleitet wurde.
"""

from django.shortcuts import redirect
from django.urls import reverse
from django.utils.http import urlencode

from . import gate


class GateMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if gate.is_exempt_path(request.path) or gate.gate_cookie_is_valid(request):
            response = self.get_response(request)
        else:
            response = self._redirect_to_gate(request)

        response["X-Robots-Tag"] = "noindex"
        return response

    @staticmethod
    def _redirect_to_gate(request):
        query = urlencode({"next": request.get_full_path()})
        return redirect(f"{reverse('gate')}?{query}")
