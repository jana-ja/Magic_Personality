"""
Markdown für Beiträge (Task 5.2, FR-B3, D-80, R-7).

Beiträge sind die erste Nutzereingabe, die andere Nutzende **gerendert**
sehen. Deshalb ist der Umfang klein und die Regel einfach: aus Markdown
entsteht nie HTML, das die Person selbst geschrieben hat.

- **Kein HTML:** `<script>`, `<img onerror=…>` und jedes andere Tag wird
  zu sichtbarem Text (`html: False`, die Regeln `html_block` und
  `html_inline` sind zusätzlich abgeschaltet).
- **Keine Bilder:** `![alt](url)` zeigt nur den Alternativtext. Ein Bild
  von fremdem Server würde bei jedem Betrachter dorthin laden (NFR-7:
  kein Tracking, keine Drittanbieter).
- **Keine Tabellen:** die Regel gehört nicht zum Preset `commonmark`.
- **Links nur `http`/`https`** (`_validate_link`): `javascript:`, `data:`,
  `vbscript:`, `file:`, `mailto:`, `//host` und relative Adressen werden
  nicht zu Links, sondern bleiben als Text stehen. Jeder Link trägt
  `rel="nofollow noopener noreferrer"` — `noreferrer` verrät der
  Zielseite nicht, woher man kam.
- **Überschriften eine Stufe tiefer:** die Beitragsseite hat mit dem
  Titel schon ihr `<h1>`; `#` im Text wird `<h2>`, höchstens `<h6>`.
- **Schachtelungstiefe begrenzt** (`maxNesting`, im Preset 20): pathologische
  Eingaben wie zehntausend `>` bleiben schnell.

Gespeichert wird nur der Markdown-Text; gerendert wird beim Anzeigen
(`render_markdown`). `render_markdown` ist die **einzige** Stelle, deren
Ergebnis als `safe` gelten darf (ARCHITECTURE §7).

Der **Auszug** (`excerpt`) entsteht aus den geparsten Tokens statt aus dem
gerenderten HTML: Es gibt kein HTML, das man wieder entschärfen müsste,
und Entities kommen schon aufgelöst an. Er ist Klartext, kein `safe` —
das Template escaped ihn wie jeden Text.
"""

import re

from django.utils.safestring import mark_safe
from markdown_it import MarkdownIt
from markdown_it.common.utils import escapeHtml

LINK_REL = "nofollow noopener noreferrer"
EXCERPT_LENGTH = 200

_ALLOWED_LINK = re.compile(r"^https?://", re.IGNORECASE)
# Was hinter ``` als Sprache durchgeht; alles andere ergibt einen Block ohne Klasse.
_LANGUAGE = re.compile(r"[\w+#.-]+")


def _validate_link(url):
    return bool(_ALLOWED_LINK.match(url.strip()))


def _harden(state):
    """Kernregel nach dem Inline-Parsen: Überschriften tiefer, Links mit `rel`,
    Codeblöcke nur mit einem echten Sprachnamen als Klasse."""
    for token in state.tokens:
        if token.type == "fence":
            language = token.info.split(maxsplit=1)[0] if token.info.strip() else ""
            token.info = language if _LANGUAGE.fullmatch(language) else ""
        if token.type in ("heading_open", "heading_close"):
            token.tag = f"h{min(int(token.tag[1]) + 1, 6)}"
        for child in token.children or ():
            if child.type == "link_open":
                child.attrSet("rel", LINK_REL)


def _render_image(self, tokens, idx, options, env):
    """Kein `<img>`: nur der Alternativtext, escaped."""
    return escapeHtml(tokens[idx].content)


def _build():
    md = MarkdownIt("commonmark", {"html": False, "linkify": False, "typographer": False})
    md.disable(["html_block", "html_inline"])
    md.validateLink = _validate_link
    md.core.ruler.push("posts_harden", _harden)
    md.add_render_rule("image", _render_image)
    return md


_md = _build()


def render_markdown(text):
    """Der Beitragstext als HTML (`SafeString`); leer oder `None` ergibt `""`."""
    if not text:
        return mark_safe("")
    return mark_safe(_md.render(text))


def _inline_text(children):
    parts = []
    for child in children or ():
        if child.type in ("text", "code_inline"):
            parts.append(child.content)
        elif child.type in ("softbreak", "hardbreak"):
            parts.append(" ")
        elif child.type == "image":
            parts.append(child.content)
    return "".join(parts)


def excerpt(text, limit=EXCERPT_LENGTH):
    """
    Klartext-Auszug für Listen und Grid: ohne Formatierung, Absätze und
    Zeilenumbrüche zu Leerzeichen, an einer Wortgrenze gekürzt und dann mit
    „…" versehen. Höchstens `limit` Zeichen plus das „…". Kein `safe`.
    """
    if not text:
        return ""
    parts = []
    for token in _md.parse(text):
        if token.type == "inline":
            parts.append(_inline_text(token.children))
        elif token.type in ("fence", "code_block"):
            parts.append(token.content)
    plain = " ".join(" ".join(parts).split())
    if len(plain) <= limit:
        return plain
    cut = plain[:limit]
    # Liegt das Limit nicht ohnehin an einer Wortgrenze, an der letzten davor
    # kürzen — außer sie liegt so früh, dass fast nichts übrig bliebe (ein
    # sehr langes Wort wird hart abgeschnitten).
    if plain[limit] != " ":
        boundary = cut.rfind(" ")
        if boundary >= limit // 2:
            cut = cut[:boundary]
    return cut.rstrip(" ,;:.-–—") + "…"
