# Magic Personality

Eine kleine Full-Stack-Webanwendung rund um das Farbrad aus *Magic: The Gathering* (WUBRG) und die Persönlichkeitseigenschaften, die den fünf Farben und ihren 31 Kombinationen zugeschrieben werden.

Ein privates, nicht-kommerzielles Spaß- und Lernprojekt für einen geschlossenen Kreis von etwa 3–10 Personen. Die Anwendung wird nicht öffentlich beworben und ist vollständig hinter einer Zugangssperre (Invite-Code) erreichbar. Kein Tracking, keine Analytics, keine Werbung.

## Funktionen

- **Color Infos** — interaktives Fünfeck zum Erkunden von Farben und Farbkombinationen: Eigenschaften, Ziele, Archetypen und die wechselseitigen Perspektiven verfeindeter Farben. Die Auswahl steht in der URL (Deep-Links), funktioniert per Maus und Tastatur und auch ohne JavaScript.
- **Personality Test** — ein Fragebogen, der die individuell stärksten Farben ermittelt; das Ergebnis lässt sich ins Profil übernehmen. Feedback zum Test ist anonym möglich.
- **Social** — Profil mit eigener Farbkombination, privater Testhistorie, Suche nach Nickname und nach Farbkombination sowie Freundschaftsanfragen und Freundeslisten.
- **Beiträge** — Beiträge in Markdown (ohne HTML aus Nutzereingaben), optional mit einer Farbkombination verknüpft; sie erscheinen im Profil und in den Color Infos.
- **Kommentare** — flache Kommentare mit festen Nummern je Beitrag und Antwort-Verweisen („↪ #n"); gelöschte Kommentare mit Antworten bleiben als Hülle stehen. Ein Zähler zeigt neue Kommentare und Antworten.
- **Pinnwand** — Beiträge und Kommentare, eigene und fremde, lassen sich an die eigene Pinnwand heften.
- Beiträge und Kommentare lassen sich melden; die Meldungen sieht nur die Projektinhaberin im Django-Admin.

Die Oberfläche ist englisch, aber i18n-fähig.

## Technik

Django-Monolith mit HTMX (Option C in [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)):

| Ebene | Wahl |
|---|---|
| Sprache / Framework | Python 3.12, Django 5.2 LTS |
| Datenbank | PostgreSQL 16 |
| Frontend | servergerendertes HTML, HTMX plus wenig eigenes JavaScript, CSS ohne Build-Schritt |
| App-Server / Statics | Gunicorn, WhiteNoise |
| Reverse Proxy | Caddy (automatisches TLS) |
| Container | Docker Compose (`web`, `db`, `caddy`) |
| Tests / Lint | pytest + pytest-django, Ruff |
| CI | GitHub Actions |

Kein Node.js, kein Bundler. Abhängigkeiten: [`requirements/`](requirements).

Die Django-Apps liegen unter [`apps/`](apps): `core` (Zugangssperre, Healthcheck), `colors`, `accounts`, `quiz`, `social`, `posts` (Beiträge, Kommentare, Pins, Meldungen).

## Lokale Entwicklung

Voraussetzungen: Python 3.12 und Docker (für PostgreSQL).

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements/dev.txt

cp .env.example .env          # Werte bei Bedarf anpassen
docker compose up -d db       # PostgreSQL, Port 5432 auf dem Host

python manage.py migrate
python manage.py seed_content --locale en
python manage.py seed_questionnaire --questionnaire-version 1 --locale en
python manage.py seed_questionnaire --questionnaire-version 2 --locale en
python manage.py runserver
```

Die Anwendung läuft dann unter <http://localhost:8000>. Beim ersten Aufruf fragt die Zugangssperre nach dem `INVITE_CODE` aus der `.env`. Die Befehle zum Einspielen der Seeds und das Format der Seed-Dateien stehen in [`seeds/README.md`](seeds/README.md) und [`seeds/questionnaire_README.md`](seeds/questionnaire_README.md).

Einen Admin-Zugang einrichten: [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md), Abschnitt „Admin-Zugang".

### Tests und Prüfungen

```bash
pytest                                  # braucht die laufende Datenbank
ruff check .
ruff format --check .
python manage.py makemigrations --check --dry-run
```

Dieselben Prüfungen (plus `manage.py check --deploy`) laufen in der CI bei jedem Pull Request gegen `main`; bei einem Push auf `main` wird zusätzlich das Container-Image gebaut und veröffentlicht.

## Deployment

Das Image kommt fertig gebaut aus der GitHub Container Registry, auf dem Server liegen nur die Compose-Dateien, das `Caddyfile` und die Skripte aus [`scripts/`](scripts):

- `scripts/deploy.sh` — schnelles Deployment ohne Schemaänderung (neues Image holen, Container erneuern)
- `scripts/deploy_full.sh` — vollständiges Deployment mit Migrationen und Seeds
- `scripts/backup.sh` — nächtliches Datenbank-Backup

Einrichtung, Backups, Wiederherstellung und Release-Hinweise je Version: [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md).

## Dokumentation

Das Projekt ist ausführlich dokumentiert; die Dokumente sind bewusst auf Deutsch und werden mit dem Code zusammen gepflegt.

| Datei | Inhalt |
|---|---|
| [`docs/PRD.md`](docs/PRD.md) | Produktanforderungen, Datenmodell, Abnahmekriterien je Meilenstein |
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | Architektur und Technologie-Entscheidung |
| [`docs/DECISIONS.md`](docs/DECISIONS.md) | Entscheidungsprotokoll (D-01 bis D-82) |
| [`docs/ROADMAP.md`](docs/ROADMAP.md) | Meilensteine und Tasks samt Umsetzungsnotizen |
| [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) | Betrieb auf dem Server |

## Hinweise

Die Farbbeschreibungen sind paraphrasiert nach [„The MTG Color Wheel"](https://homosabiens.substack.com/p/the-mtg-color-wheel) von Duncan Sabien.

Magic Personality ist inoffizieller Fan Content, zulässig nach der Wizards of the Coast Fan Content Policy. Nicht von Wizards genehmigt oder unterstützt. Teile der verwendeten Materialien sind Eigentum von Wizards of the Coast. © Wizards of the Coast LLC.

Eine Lizenz für den Quellcode ist derzeit nicht festgelegt.
