"""
Projektweite pytest-Fixtures.

Bisher nur eine: ein Client, der die Zugangssperre aus Task 0.5 schon
passiert hat. Jede fachliche Seite liegt hinter dem Gate (FR-A1), ein
nackter `client` bekommt dort also eine Weiterleitung statt der Seite.
"""

import pytest
from django.conf import settings

from apps.core import gate


@pytest.fixture
def gated_client(client):
    """Test-Client mit gültigem Gate-Cookie (Task 0.5, FR-A1)."""
    client.cookies[settings.GATE_COOKIE_NAME] = gate.sign_gate_cookie()
    return client
