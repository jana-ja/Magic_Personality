"""
Tests für das Basis-Template (Task 0.4).

Prüft strukturelle Bausteine (HTMX eingebunden, CSRF-Header gesetzt)
sowie stichprobenartig, dass sichtbarer Text tatsächlich durch
gettext läuft statt hart codiert im Template zu stehen — genau das
verlangt die Definition of Done ("Stichprobe reicht").
"""

from django.template import base as template_base
from django.template.loader import render_to_string


def _render_base(request):
    return render_to_string("base.html", {}, request=request)


def test_base_template_includes_htmx_and_csrf_header(rf):
    html = _render_base(rf.get("/"))

    assert 'src="/static/js/htmx.min.js"' in html
    assert "X-CSRFToken" in html


def test_base_template_has_header_main_and_footer_landmarks(rf):
    html = _render_base(rf.get("/"))

    assert "<header" in html
    assert 'id="main-content"' in html
    assert "<footer" in html


def test_base_template_has_a_skip_link_for_keyboard_users(rf):
    html = _render_base(rf.get("/"))

    assert 'href="#main-content"' in html


def test_visible_text_goes_through_gettext(monkeypatch, rf):
    """
    Ersetzt gettext_lazy (das `{% translate %}` beim Rendern eines
    Literals tatsächlich aufruft, siehe django/template/base.py) durch
    eine Markierungsfunktion. Landet die Markierung im gerenderten
    HTML, kam der Text durch die Übersetzungsmaschinerie statt als
    hart codierter String im Template zu stehen.
    """

    def _marked(msgid, *args, **kwargs):
        return f"[[{msgid}]]"

    monkeypatch.setattr(template_base, "gettext_lazy", _marked)

    html = _render_base(rf.get("/"))

    assert "[[Magic Personality]]" in html
    assert "[[Skip to main content]]" in html
    assert "[[A small, private project about the Magic: The Gathering color wheel.]]" in html
