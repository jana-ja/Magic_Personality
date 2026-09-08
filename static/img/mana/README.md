# Mana-Symbole

Die fünf offiziellen Mana-Symbole, eingebunden mit Task 1.5 (FR-C2).

## Erwartete Dateien

| Datei | Farbe | `Color.symbol` |
|---|---|---|
| `w.svg` | White | `img/mana/w.svg` |
| `u.svg` | Blue | `img/mana/u.svg` |
| `b.svg` | Black | `img/mana/b.svg` |
| `r.svg` | Red | `img/mana/r.svg` |
| `g.svg` | Green | `img/mana/g.svg` |

Der Dateiname ist der Farbcode in Kleinschreibung. `Color.symbol` hält
den Pfad **relativ zu `static/`** — also genau das, was `{% static %}`
erwartet. Kein führender Schrägstrich, kein `static/`-Präfix.

## Format

SVG bevorzugt: Das Fünfeck ist selbst SVG, die Symbole skalieren dort
verlustfrei mit und funktionieren in jeder Ecke gleich gut. PNG ginge
auch, bräuchte dann aber eine @2x-Fassung für hochauflösende Displays.

Die Symbole tragen ihre eigenen Farben und werden nicht per CSS
umgefärbt — Einbindung als `<img>` beziehungsweise `<image>` innerhalb
des Fünfecks reicht, kein Inlining nötig.

## Warum hier und nicht in `staticfiles/`

`static/` ist das versionierte Quellverzeichnis (`STATICFILES_DIRS`).
`staticfiles/` ist der Ausgabeordner von `collectstatic`, steht in
`.gitignore` und wird beim Deployment neu erzeugt — dort abgelegte
Dateien wären beim nächsten Build weg.

In Produktion läuft WhiteNoise mit `CompressedManifestStaticFilesStorage`
(`config/settings/prod.py`): Dateinamen bekommen beim Sammeln einen
Hash. Pfade deshalb **immer** über `{% static %}` auflösen, nie fest
eintragen — sonst brechen sie im Deployment.

## Herkunft und Rechtliches

Verwendung unter der *Wizards of the Coast Fan Content Policy* (D-12,
PRD §9). Voraussetzung ist durchgehende Nicht-Kommerzialität; der
vorgeschriebene Hinweis steht im Footer (Task 1.5).
