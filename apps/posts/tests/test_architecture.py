"""
Prüfungen gegen ARCHITECTURE.md (Task 5.9, D-78, D-80, PRD R-7).

Das sind keine Verhaltenstests, sondern Wächter für Regeln, die sich sonst
unbemerkt aufweichen: Sie lesen den Quelltext. Schlägt einer an, gehört die
Änderung bewusst begründet (Eintrag in `docs/DECISIONS.md`), nicht der Test
stillschweigend angepasst.
"""

import re
from pathlib import Path

from django.conf import settings

BASE = Path(settings.BASE_DIR)


def _sources(pattern, *, skip=("tests", "migrations")):
    for path in sorted(BASE.glob(pattern)):
        if not any(part in skip for part in path.parts):
            yield path


def _python():
    return _sources("apps/**/*.py")


def _templates():
    return _sources("templates/**/*.html", skip=())


def test_no_code_reads_posts_around_visible_to():
    """Jeder lesende Zugriff geht durch `Post.objects.visible_to(profile)` (FR-B9, D-78): nur so
    ist „nur Freunde" später eine Änderung an einer Stelle. Erlaubt bleiben Schreibzugriffe
    (`create`). Auch der Umweg über den Related Manager (`profile.posts.…`) zählt."""
    direct = re.compile(r"\bPost\.objects\.(?!visible_to\b|create\b)")
    related = re.compile(
        r"\.posts\.(all|filter|exclude|get|first|last|count|exists|order_by|values|"
        r"select_related|prefetch_related)\b"
    )
    offenders = []
    for path in [*_python(), *_templates()]:
        text = path.read_text(encoding="utf-8")
        for number, line in enumerate(text.splitlines(), start=1):
            if direct.search(line) or related.search(line):
                offenders.append(f"{path.relative_to(BASE)}:{number}: {line.strip()}")

    assert offenders == [], "\n".join(offenders)


def test_user_text_is_never_marked_safe_except_by_render_markdown():
    """Nutzereingaben werden nur über `apps/posts/markdown.py` als `safe` ausgegeben (D-80,
    ARCHITECTURE §7): kein `|safe`, kein `{% autoescape off %}`, `mark_safe` nur dort."""
    offenders = []
    for path in _templates():
        text = path.read_text(encoding="utf-8")
        if re.search(r"\|\s*safe\b|autoescape\s+off|\|\s*safeseq\b", text):
            offenders.append(str(path.relative_to(BASE)))
    for path in _python():
        text = path.read_text(encoding="utf-8")
        if re.search(r"\bmark_safe\(|\bSafeString\(|\bSafeText\(", text) and (
            path.relative_to(BASE).as_posix() != "apps/posts/markdown.py"
        ):
            offenders.append(str(path.relative_to(BASE)))

    assert offenders == [], offenders


def test_the_only_new_dependency_is_markdown_it_py():
    """ARCHITECTURE §3 und §13: jede Abhängigkeit ist eine Entscheidung (D-80)."""
    names = set()
    for line in (BASE / "requirements" / "base.txt").read_text().splitlines():
        line = line.split("#")[0].strip()
        if line:
            names.add(re.split(r"[<>=!\[ ]", line, maxsplit=1)[0].lower())

    assert names == {
        "django",
        "django-environ",
        "psycopg",
        "argon2-cffi",
        "django-axes",
        "markdown-it-py",
    }


def test_posts_does_not_depend_on_social():
    """D-78: `colors` und `social` lesen aus `posts`, nicht umgekehrt. (Ein Template darf die
    Autorenkarte aus `social` einbinden; Python-Code der Posts-App importiert `social` nicht.)"""
    offenders = [
        str(path.relative_to(BASE))
        for path in _python()
        if path.relative_to(BASE).parts[1] == "posts"
        and re.search(r"^\s*(from|import)\s+apps\.social\b", path.read_text(), re.M)
    ]

    assert offenders == [], offenders
