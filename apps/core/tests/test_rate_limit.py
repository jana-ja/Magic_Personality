"""
Tests für apps.core.rate_limit.client_ip() (Task 1.12, D-51).

Prüft nur die IP-Ermittlung, nicht is_rate_limited()/rate_limit() —
deren Zählungslogik ist bereits über die Gate-Tests (Task 0.5)
abgedeckt.
"""

from django.test import RequestFactory

from apps.core.rate_limit import client_ip


def test_client_ip_falls_back_to_remote_addr_without_a_proxy_header():
    """Lokale Entwicklung/Tests: kein Caddy davor, kein X-Forwarded-For."""
    request = RequestFactory().get("/", REMOTE_ADDR="203.0.113.5")

    assert client_ip(request) == "203.0.113.5"


def test_client_ip_uses_the_last_forwarded_for_entry():
    """
    Caddy ERGÄNZT X-Forwarded-For um den von ihm gesehenen Peer, statt
    einen vom Client mitgeschickten Wert zu ersetzen — der letzte
    Eintrag ist deshalb immer Caddys eigene, vertrauenswürdige
    Beobachtung, unabhängig davon, was ein Client selbst voranstellt.
    """
    request = RequestFactory().get(
        "/",
        REMOTE_ADDR="10.0.0.2",  # Caddys eigene Container-IP im Compose-Netz
        HTTP_X_FORWARDED_FOR="203.0.113.5",
    )

    assert client_ip(request) == "203.0.113.5"


def test_client_ip_ignores_a_spoofed_leading_entry():
    """
    Ein Client, der selbst einen X-Forwarded-For-Header mitschickt, um
    sich eine andere IP vorzutäuschen — Caddy hängt seine eigene
    Beobachtung dahinter an, genau die zählt.
    """
    request = RequestFactory().get(
        "/",
        REMOTE_ADDR="10.0.0.2",
        HTTP_X_FORWARDED_FOR="198.51.100.9, 203.0.113.5",
    )

    assert client_ip(request) == "203.0.113.5"
