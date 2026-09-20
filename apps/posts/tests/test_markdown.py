"""
Tests für das Markdown-Rendering (Task 5.2, FR-B3, D-80, PRD R-7).

Kern ist der Injektionstest: jede Eingabe aus `INJECTION_CORPUS` wird
gerendert, und die Ausgabe muss eine **Positivliste** einhalten (erlaubte
Tags, erlaubte Attribute mit erlaubten Werten). Das prüft mehr als das
Fehlen bekannter Zeichenketten: auch ein unerwartetes Tag oder Attribut
fiele auf.
"""

import re
import time
from html.parser import HTMLParser

import pytest
from django.template import Context, Template
from django.utils.safestring import SafeString

from apps.posts.markdown import EXCERPT_LENGTH, LINK_REL, excerpt, render_markdown

ALLOWED_TAGS = {
    "p", "br", "em", "strong", "code", "pre", "blockquote", "ul", "ol", "li", "hr",
    "a", "h2", "h3", "h4", "h5", "h6",
}  # fmt: skip

# Tag -> Attribut -> Muster, dem der Wert vollständig entsprechen muss.
ALLOWED_ATTRIBUTES = {
    "a": {"href": r"https?://[^\s<>\"']*", "rel": re.escape(LINK_REL), "title": r".*"},
    "code": {"class": r"language-[\w+#.-]+"},
    "ol": {"start": r"\d+"},
}


class _Validator(HTMLParser):
    """Wirft `AssertionError` bei jedem Tag oder Attribut außerhalb der Positivliste."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.link_count = 0

    def handle_starttag(self, tag, attrs):
        assert tag in ALLOWED_TAGS, f"unexpected tag <{tag}>"
        allowed = ALLOWED_ATTRIBUTES.get(tag, {})
        for name, value in attrs:
            assert name in allowed, f"unexpected attribute {name!r} on <{tag}>"
            assert re.fullmatch(allowed[name], value or ""), f"bad {name}={value!r} on <{tag}>"
        if tag == "a":
            self.link_count += 1
            assert dict(attrs).get("rel") == LINK_REL, "link without rel"
            assert "href" in dict(attrs), "link without href"

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)

    def handle_comment(self, data):
        raise AssertionError("HTML comment in output")

    def handle_decl(self, decl):
        raise AssertionError("declaration in output")

    def handle_pi(self, data):
        raise AssertionError("processing instruction in output")

    def unknown_decl(self, data):
        raise AssertionError("CDATA in output")


def assert_only_allowed_markup(html):
    validator = _Validator()
    validator.feed(html)
    validator.close()
    return validator


INJECTION_CORPUS = [
    # Roh-HTML: wird zu sichtbarem Text
    "<script>alert(1)</script>",
    "<SCRIPT SRC=http://evil.example/x.js></SCRIPT>",
    "<img src=x onerror=alert(1)>",
    "<svg onload=alert(1)>",
    "<iframe src=javascript:alert(1)></iframe>",
    "<style>body{display:none}</style>",
    '<div onclick="alert(1)">click</div>',
    '<a href="javascript:alert(1)">x</a>',
    "<!-- comment --><b>x</b>",
    "<![CDATA[ <script>alert(1)</script> ]]>",
    "<?php echo 1; ?>",
    "<form action=http://evil.example><input name=x></form>",
    "<meta http-equiv=refresh content='0;url=http://evil.example'>",
    "<base href=http://evil.example/>",
    "<math><mi xlink:href=javascript:alert(1)>x</mi></math>",
    # gefährliche Link-Adressen
    "[x](javascript:alert(1))",
    "[x](JaVaScRiPt:alert(1))",
    "[x](  javascript:alert(1))",
    "[x](java&#x09;script:alert(1))",
    "[x](&#106;avascript:alert(1))",
    "[x](jav\tascript:alert(1))",
    "[x](data:text/html;base64,PHNjcmlwdD5hbGVydCgxKTwvc2NyaXB0Pg==)",
    "[x](vbscript:msgbox(1))",
    "[x](file:///etc/passwd)",
    "[x](//evil.example/x)",
    "[x](/relative/path)",
    "[x](mailto:someone@example.com)",
    "[x](ｊavascript:alert(1))",
    "<javascript:alert(1)>",
    "[x][1]\n\n[1]: javascript:alert(1)",
    '[x](http://a.example "t" onmouseover="alert(1)")',
    '[x](http://a.example "title\\" onmouseover=\\"alert(1)")',
    "[x](<http://a.example/a b>)",
    '[x](http://a.example/"onmouseover=alert(1))',
    # Bilder
    "![x](http://evil.example/track.png)",
    "![x](javascript:alert(1))",
    '![x](y "onerror=alert(1)")',
    "![<script>alert(1)</script>](http://evil.example/x.png)",
    "![x][1]\n\n[1]: http://evil.example/x.png",
    # Entities und Escapes
    "&lt;script&gt;alert(1)&lt;/script&gt;",
    "&#60;script&#62;alert(1)&#60;/script&#62;",
    "&#x3C;img src=x onerror=alert(1)&#x3E;",
    "\\<script>alert(1)\\</script>",
    # Code-Blöcke mit Info-String
    '```"><script>alert(1)</script>\ncode\n```',
    "```js onmouseover=alert(1)\ncode\n```",
    "~~~ <img src=x onerror=alert(1)>\ncode\n~~~",
    "    <script>alert(1)</script>",
    "`<script>alert(1)</script>`",
    # Überschriften, Listen, Zitate mit HTML
    "# <script>alert(1)</script>",
    "Title\n=====\n<script>alert(1)</script>",
    "- <img src=x onerror=alert(1)>\n- [x](javascript:1)",
    "> <script>alert(1)</script>\n> [x](javascript:1)",
    "3. item <b onclick=1>x</b>",
    # Unvollständig und verschachtelt
    "[[[[[x](javascript:1)",
    "*a **b _c",
    "<" * 500,
    "[" * 500 + "x" + "](javascript:1)" * 3,
    "> " * 60 + "<script>alert(1)</script>",
    "- " * 60 + "<script>alert(1)</script>",
    "\x00<script>alert(1)</script>",
    "<scr\x00ipt>alert(1)</scr\x00ipt>",
]


@pytest.mark.parametrize("markdown", INJECTION_CORPUS)
def test_injection_corpus_never_becomes_markup(markdown):
    html = render_markdown(markdown)

    assert_only_allowed_markup(html)
    lowered = html.lower()
    # Nur Tags, die es als Markup nicht geben darf. Wörter wie „onerror" dürfen
    # als sichtbarer, escapter Text vorkommen; ob daraus ein Attribut wurde,
    # entscheidet die Positivliste oben.
    for forbidden in ("<script", "<img", "<iframe", "<svg", "<style"):
        assert forbidden not in lowered
    assert 'href="javascript' not in lowered
    assert "href='javascript" not in lowered


@pytest.mark.parametrize("markdown", INJECTION_CORPUS)
def test_injection_corpus_is_harmless_in_the_excerpt_too(markdown):
    """Der Auszug ist Klartext; das Template escaped ihn. Maßgeblich ist die
    fertig gerenderte Seite, nicht der rohe Rückgabewert."""
    result = excerpt(markdown)
    assert type(result) is str  # kein SafeString: Autoescape gilt

    page = Template("{% load posts_tags %}<p>{{ body|excerpt }}</p>").render(
        Context({"body": markdown})
    )

    assert_only_allowed_markup(page)


@pytest.mark.parametrize("markdown", INJECTION_CORPUS)
def test_injection_corpus_is_harmless_through_the_template_filter(markdown):
    page = Template("{% load posts_tags %}{{ body|markdown }}").render(Context({"body": markdown}))

    assert_only_allowed_markup(page)


def test_fence_info_string_only_becomes_a_class_when_it_is_a_language_name():
    plain = render_markdown("```python\nx\n```")
    weird = render_markdown('```"><script>alert(1)</script>\nx\n```')
    extra = render_markdown("```js onmouseover=alert(1)\nx\n```")

    assert '<code class="language-python">' in plain
    assert "<code>" in weird
    assert '<code class="language-js">' in extra
    assert "onmouseover" not in extra


def test_the_validator_itself_catches_dangerous_markup():
    """Schutz vor einem Test, der nichts prüft: die Positivliste schlägt an."""
    for bad in (
        "<script>alert(1)</script>",
        '<img src="x">',
        f'<a href="javascript:alert(1)" rel="{LINK_REL}">x</a>',
        '<a href="https://x.example">x</a>',
        '<p onclick="1">x</p>',
        "<!-- c -->",
    ):
        with pytest.raises(AssertionError):
            assert_only_allowed_markup(bad)


# Erlaubter Umfang ---------------------------------------------------------------


def test_basic_formatting_is_rendered():
    html = render_markdown("**bold** and *italic* and `code`")

    assert html == "<p><strong>bold</strong> and <em>italic</em> and <code>code</code></p>\n"


def test_lists_quotes_and_code_blocks_are_rendered():
    html = render_markdown(
        "- one\n- two\n\n1. first\n2. second\n\n> quoted\n\n```python\nx = 1\n```"
    )

    for tag in ("<ul>", "<ol>", "<blockquote>", "<pre>", '<code class="language-python">'):
        assert tag in html
    assert_only_allowed_markup(html)


def test_headings_start_one_level_lower_and_stop_at_six():
    html = render_markdown("# one\n\n## two\n\n###### six\n\nSetext\n======")

    assert "<h2>one</h2>" in html
    assert "<h3>two</h3>" in html
    assert "<h6>six</h6>" in html
    assert "<h2>Setext</h2>" in html
    assert "<h1" not in html
    assert "<h7" not in html


def test_the_result_is_marked_safe_and_plain_text_is_escaped():
    html = render_markdown("1 < 2 & 3 > 2")

    assert isinstance(html, SafeString)
    assert html == "<p>1 &lt; 2 &amp; 3 &gt; 2</p>\n"


@pytest.mark.parametrize("empty", ["", None])
def test_empty_input_renders_nothing(empty):
    assert render_markdown(empty) == ""
    assert excerpt(empty) == ""


# Links --------------------------------------------------------------------------


@pytest.mark.parametrize("url", ["http://example.com/a?b=1&c=2", "https://example.com"])
def test_http_and_https_links_are_rendered_with_rel(url):
    html = render_markdown(f"[text]({url})")

    assert 'href="' + url.replace("&", "&amp;") + '"' in html
    assert f'rel="{LINK_REL}"' in html
    assert assert_only_allowed_markup(html).link_count == 1


def test_autolinks_get_the_same_treatment():
    html = render_markdown("<https://example.com>")

    assert f'rel="{LINK_REL}"' in html
    assert assert_only_allowed_markup(html).link_count == 1


@pytest.mark.parametrize(
    "target",
    [
        "javascript:alert(1)",
        "data:text/plain,hi",
        "vbscript:x",
        "file:///etc/passwd",
        "mailto:a@example.com",
        "//example.com",
        "/colors/wg/",
        "example.com",
    ],
)
def test_every_other_target_stays_as_text_and_is_not_a_link(target):
    html = render_markdown(f"[text]({target})")

    assert "<a" not in html
    assert assert_only_allowed_markup(html).link_count == 0
    assert "[text]" in html


# Bilder -------------------------------------------------------------------------


def test_images_show_only_their_alt_text():
    html = render_markdown("before ![a diagram](https://example.com/x.png) after")

    assert "<img" not in html
    assert "a diagram" in html
    assert "example.com/x.png" not in html
    assert_only_allowed_markup(html)


def test_alt_text_is_escaped():
    html = render_markdown("![<b>x</b>](https://example.com/x.png)")

    assert "<b>" not in html
    assert "&lt;b&gt;x&lt;/b&gt;" in html


# Auszug -------------------------------------------------------------------------


def test_short_text_is_returned_unchanged_without_formatting():
    assert excerpt("Some **bold** text with a [link](https://example.com).") == (
        "Some bold text with a link."
    )


def test_blocks_are_separated_by_spaces():
    text = "# Heading\n\nParagraph one\nsecond line\n\n- item a\n- item b\n\n> quote"

    assert excerpt(text) == "Heading Paragraph one second line item a item b quote"


def test_code_is_kept_as_text():
    assert excerpt("Use `print()` here\n\n```\nx = 1\n```") == "Use print() here x = 1"


def test_entities_arrive_resolved_and_html_stays_text():
    assert excerpt("Fish &amp; chips <b>x</b>") == "Fish & chips <b>x</b>"


def test_images_contribute_their_alt_text_only():
    assert excerpt("see ![a diagram](https://example.com/x.png)") == "see a diagram"


def test_long_text_is_cut_at_a_word_boundary_with_an_ellipsis():
    text = "word " * 100

    result = excerpt(text, limit=50)

    assert result.endswith("…")
    assert len(result) <= 51
    assert result == ("word " * 10).strip() + "…"
    assert " …" not in result


def test_default_limit_is_about_two_hundred_characters():
    result = excerpt("lorem ipsum " * 100)

    assert EXCERPT_LENGTH == 200
    assert len(result) <= EXCERPT_LENGTH + 1
    assert result.endswith("…")


def test_a_very_long_word_is_cut_hard():
    result = excerpt("x" * 500, limit=100)

    assert result == "x" * 100 + "…"


def test_trailing_punctuation_is_not_left_before_the_ellipsis():
    result = excerpt("alpha beta, gamma delta", limit=11)

    assert result == "alpha beta…"


def test_text_exactly_at_the_limit_gets_no_ellipsis():
    assert excerpt("x" * 50, limit=50) == "x" * 50


def test_markup_only_input_gives_an_empty_excerpt():
    assert excerpt("---\n\n***") == ""


# Robustheit -----------------------------------------------------------------------


@pytest.mark.parametrize(
    "pathological",
    [
        "> " * 5000,
        "- " * 5000,
        "[" * 10_000,
        "*" * 10_000,
        "*a " * 3000,
        "`" * 10_000,
        "<" * 10_000,
        "[a](" * 2500,
        "1. " * 3000,
    ],
)
def test_pathological_input_stays_fast_and_safe(pathological):
    started = time.monotonic()

    html = render_markdown(pathological)
    excerpt(pathological)

    assert time.monotonic() - started < 2
    assert_only_allowed_markup(html)
