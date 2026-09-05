# Architektur — Magic Personality

**Status:** Festgelegt · **Datum:** 2026-09-06 · Grundlage: `docs/PRD.md` · Auswahl aus `docs/ARCHITECTURE_OPTIONS.md`

---

## 1. Entscheidung

**Option C — Django-Monolith mit HTMX**, PostgreSQL, Docker Compose, Caddy.

Ein Deploy-Artefakt, eine Sprache, servergerendertes HTML. Auth, Sessions, Migrations, i18n und ein Rechte-Grundgerüst kommen aus dem Framework.

### 1.1 Bewusst in Kauf genommen

| Schwäche | Umgang |
|---|---|
| Geringerer DevOps-Lernwert als bei getrennten Artefakten | Wird gezielt zurückgeholt: Reverse Proxy mit TLS, Migrations als eigener Deploy-Schritt, CI-Pipeline, Backups, definierter Cloud-Migrationspfad (§11, §12). Der Betrieb wird nicht vereinfacht, nur weil die Anwendung es zulässt. |
| Das Fünfeck passt nicht ins Template-Paradigma | Gelöst über Progressive Enhancement statt über eine React-Insel (§4). Das ist ein **besserer** Ansatz als der im Vergleichsdokument skizzierte — kein zweites Paradigma, keine doppelte Renderlogik. |

---

## 2. Systemüberblick

```
                    ┌──────────────────────────────────┐
[ Browser ] ──TLS──>│ Caddy (Reverse Proxy, Let's Enc.)│
                    └───────────────┬──────────────────┘
                                    │
                    ┌───────────────▼──────────────────┐
                    │ Django + Gunicorn                │
                    │  ├─ core     (Gate, Health)      │
                    │  ├─ colors   (Farben, Kombis)    │
                    │  ├─ accounts (User, Profile)     │
                    │  ├─ quiz     (Test)              │
                    │  └─ social   (Suche, Freunde)    │
                    └───────────────┬──────────────────┘
                                    │
                    ┌───────────────▼──────────────────┐
                    │ PostgreSQL  (Daten + Sessions)   │
                    └──────────────────────────────────┘
```

Drei Container: `web`, `db`, `caddy`. Kein Redis, kein separater Worker, kein Node-Prozess zur Laufzeit.

---

## 3. Technologie-Stack

| Ebene | Wahl | Begründung |
|---|---|---|
| Sprache | Python 3.12 | |
| Framework | Django 5.2 LTS | LTS bedeutet lange Wartungsruhe — passend für ein Nebenprojekt |
| Datenbank | PostgreSQL 16 | Array-Felder und JSON-Felder für Farbmengen und Punktstände |
| Interaktivität | **HTMX** (~14 kB) + ca. 100 Zeilen eigenes JavaScript | siehe §4 |
| CSS | Modernes CSS mit Custom Properties, **kein Build-Schritt** | Zwei eigenständige Layouts (NFR-3) sind mit Media Queries direkter lösbar als mit Utility-Klassen — und es spart die gesamte Node-Toolchain |
| App-Server | Gunicorn | |
| Statische Dateien | WhiteNoise | Ein Artefakt weniger im Deployment |
| Reverse Proxy | Caddy | Automatisches TLS mit minimaler Konfiguration |
| Tests | pytest + pytest-django | |
| Linting | Ruff (Lint + Format) | Ein Werkzeug statt drei |
| Container | Docker + Compose | |
| CI | GitHub Actions | |

**Kein Node.js, kein Bundler, kein npm.** Das ist der größte Einzelgewinn dieser Wahl: der Container enthält eine Laufzeit, das Deployment einen Build-Schritt.

---

## 4. Frontend-Strategie: Progressive Enhancement statt JS-Insel

Das Fünfeck ist das Kernstück und der schwierigste Teil. Statt eine React-Komponente in eine Template-Welt zu setzen (zwei Paradigmen, Renderlogik doppelt), wird es **serverseitig** gerendert und clientseitig nur beschleunigt.

### 4.1 Funktionsweise

Jede Farbe im Fünfeck ist ein Link auf die Ziel-URL, die sich beim Umschalten dieser Farbe ergibt:

```html
<!-- Aktuell /colors/wu/ — Klick auf Black führt zu /colors/wub/ -->
<a href="/colors/wub/"
   hx-get="/colors/wub/"
   hx-target="#info-panel"
   hx-select="#info-panel"
   hx-push-url="true"
   role="button" aria-pressed="false">…</a>
```

- **Ohne JavaScript:** normaler Seitenaufruf. Alles funktioniert, nur langsamer.
- **Mit HTMX:** nur das Info-Panel wird getauscht, die URL wird per `pushUrl` aktualisiert.
- **Zurück-Navigation** funktioniert in beiden Fällen, weil der Zustand immer in der URL steht.

### 4.2 Warum das besser passt als eine JS-Insel

| | JS-Insel (React) | Progressive Enhancement |
|---|---|---|
| Renderlogik für Kombi-Infos | zweimal (Template + JS) | einmal (Template) |
| i18n der Inhalte | eigener Weg im JS nötig | Djangos i18n greift direkt |
| URL-Zustand (FR-C7) | manuell zu verdrahten | ist der Normalfall |
| Barrierefreiheit (NFR-5) | selbst herzustellen | echte Links, funktionieren von Haus aus |
| Build-Schritt | Node-Toolchain | keiner |

Die Anforderung „kein SEO nötig" (T4) macht SSR nicht wertlos — sie macht es hier nur zum *einfacheren* Weg statt zum performanteren.

### 4.3 Das eigene JavaScript

Ungefähr 100 Zeilen, ohne Framework:

1. **Tastaturkürzel** (FR-C8): `W U B R G` lösen einen Klick auf den zugehörigen Link aus, `Esc` auf „Zurücksetzen". Mehr ist es nicht.
2. **Optimistische Hervorhebung:** Die Farbmarkierung im Fünfeck wird sofort umgeschaltet, bevor die Antwort da ist. Der Server-Zustand korrigiert das anschließend.
3. **Live-Region** (NFR-5): Nach dem HTMX-Swap wird der neue Kombinationsname angesagt.

### 4.4 Fünfeck-Geometrie

Ein handgeschriebenes SVG mit fünf Positionen, aus `wheel_position` berechnet. Positionen liegen in **einer** Konstante — damit stimmen Nachbarschaften, `leaning_toward`-Richtungen und die Darstellung immer überein und lassen sich in einem Test gegen die Datenbank prüfen.

Mobil (NFR-3): ein eigenes Template-Fragment. Fünfeck oben, Infoblock darunter, Eigenschaften **nicht** am Fünfeck verortet. Umschaltung per Media Query auf CSS-Ebene; wo die Struktur zu verschieden ist, per `{% include %}` zweier Fragmente.

---

## 5. Projektstruktur

```
magic_personality/
├── config/              # settings/, urls.py, wsgi.py
│   └── settings/        # base.py, dev.py, prod.py
├── apps/
│   ├── core/            # Invite-Gate-Middleware, Healthcheck, Basis-Templates
│   ├── colors/          # Color, ColorCombination, Trait, CombinationTrait, Perspective
│   ├── accounts/        # User, Profile, ColorAssignment, Auth-Views, Avatar
│   ├── quiz/            # Questionnaire, Question, AnswerOption, TestResult, Auswertung
│   └── social/          # Friendship, Suche
├── locale/              # Übersetzungskataloge (NFR-4)
├── static/              # CSS, htmx.min.js, eigenes JS, Mana-Symbole
├── templates/
├── seeds/               # Content als versionierte JSON-Dateien (§9)
├── tests/
├── docs/
├── compose.yaml
├── Dockerfile
└── Caddyfile
```

---

## 6. Datenmodell in Django

Setzt §6 des PRD um. Django-spezifische Festlegungen:

### 6.1 Eigenes User-Modell ab der ersten Migration
Django lässt sich das User-Modell später **nicht** ohne Weiteres austauschen. Deshalb ab Tag eins:

```python
class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    USERNAME_FIELD = "email"
```

Kein `username`-Feld — der Nickname gehört laut PRD an `Profile`, nicht an den Account. `PermissionsMixin` bleibt drin, weil das Kuratoren-Konzept (§8.2 PRD) genau darauf aufsetzen wird.

### 6.2 Farbmengen als kanonischer Code
`ColorCombination.code` ist die in WUBRG-Reihenfolge sortierte Buchstabenfolge: `"W"`, `"WU"`, `"WUBRG"`. Eindeutig, direkt die URL aus FR-C7, und alle 31 Zeilen werden vorab angelegt.

Daraus folgt eine Vereinfachung gegenüber dem PRD-Entwurf: **`ColorAssignment` verweist per Fremdschlüssel auf `ColorCombination`.** Die Farben einer Person *sind* eine der 31 Kombinationen — keine zweite Darstellung von Farbmengen im System.

Die Teilmengen-Suche aus FR-S3 wird damit zu einer Kette von Buchstaben-Prüfungen auf `code` (Suche „WU" → `code` enthält `W` **und** `U`). Bei 31 möglichen Werten und 10 Profilen ist das mehr als ausreichend; es lässt sich später ohne Schemaänderung durch eine Vorab-Auflösung der passenden Codes ersetzen.

### 6.3 Ally/Enemy
Reine Berechnung aus `wheel_position` (FR-C9), als Eigenschaft am Modell, nicht als Spalte.

### 6.4 Weitere Festlegungen
- `TestResult.scores` als `JSONField` — `{"W": 5, "U": 3, ...}`.
- `Trait.type` und `ColorAssignment.source` als `TextChoices`.
- `Profile.user` ist `OneToOneField(null=True)` — bereitet fremd angelegte Profile vor (§8.1 PRD).
- `Friendship` mit Constraint auf die geordnete Paarung, damit dieselbe Freundschaft nicht doppelt entstehen kann.
- Nickname-Eindeutigkeit über einen funktionalen Unique-Index auf `Lower("nickname")` (FR-P2).

---

## 7. Auth und Sicherheit

| Anforderung | Umsetzung |
|---|---|
| Sessions (FR-U4) | Djangos Session-Framework, `django.contrib.sessions.backends.db`. `SESSION_COOKIE_HTTPONLY`, `_SECURE`, `_SAMESITE="Lax"` |
| Alle Sessions bei Passwortänderung beenden (FR-U5) | Djangos Session-Auth-Hash — Standardverhalten, kein eigener Code |
| Passwort-Hashing (FR-U2) | Argon2 (`django[argon2]`) |
| CSRF (NFR-8) | Djangos Middleware; HTMX sendet den Token über `hx-headers` global |
| Rate Limiting (FR-U6) | `django-axes` für Login-Versuche, eigener Decorator für Registrierung und Invite-Gate |
| Invite-Gate (FR-A1) | Eigene Middleware, prüft ein signiertes Cookie. Freigelistet: Gate-View, Healthcheck, statische Dateien. **Alles** andere ist gesperrt, auch API-Pfade |
| Kein Passwort-Reset (FR-U7) | Djangos Reset-URLs werden nicht eingebunden. Zurücksetzen per Management-Command auf dem Server |
| Account-Löschung (FR-U8) | View mit Bestätigung; `on_delete=CASCADE` auf Profile, TestResult, ColorAssignment, Friendship |
| `noindex` (FR-A4) | Header über Middleware plus `robots.txt` |

---

## 8. Mehrsprachigkeit

- **UI-Texte:** Djangos `gettext`, Kataloge unter `locale/`. Kein Anzeigetext ohne Übersetzungsaufruf.
- **Inhalte:** `locale`-Spalte auf `ColorCombination`, `Trait`, `Perspective`, `Question`, `AnswerOption` (§6.3 PRD); eindeutig ist jeweils fachlicher Schlüssel plus Locale. Ein Manager liefert Zeilen in der aktiven Sprache mit Rückfall auf `en`.
- Ausgeliefert wird in v1 nur `en`; `LocaleMiddleware` ist aber von Anfang an aktiv, damit die Sprachauflösung nicht nachträglich eingezogen werden muss.

Bewusst **kein** `django-modeltranslation`: Die eigene `locale`-Spalte ist im PRD festgelegt, verständlicher und ohne Abhängigkeit.

---

## 9. Content-Seeding

Der Farb-Content liegt als versionierte JSON-Dateien unter `seeds/` im Repository und wird per Management-Command idempotent eingespielt:

```bash
python manage.py seed_content --locale en
```

- Reproduzierbar, im Review sichtbar, in CI testbar.
- Das Erfassen aus der Quelle (§9 PRD) ist ein eigener Task in v0.1 und ersetzt die bestehende KI-generierte JSON-Datei.
- **Django Admin ist zusätzlich verfügbar** für punktuelle Korrekturen — aber die Seeds bleiben die Wahrheit. Wer nur im Admin korrigiert, verliert die Änderung beim nächsten Aufsetzen.
- Der Fragebogen wird genauso behandelt: `seeds/questionnaire_v1.json`, unveränderlich nach Veröffentlichung (FR-T6).

---

## 10. Tests

Schwerpunkt auf den Regeln, die inhaltlich falsch sein *können* — nicht auf Django selbst:

- **Fragebogen-Balance (FR-T3):** Jedes der 10 Farbpaare kommt genau zweimal vor, jede Farbe in genau 8 Fragen. Läuft gegen die Seed-Datei, nicht gegen Beispieldaten.
- **Auswertungsregel (FR-T10 bis FR-T12):** Tabellengetriebene Fälle — klarer Dreier, deutlicher Zweier, deutlicher Vierer, Gleichstand an der Grenze, Gleichstand über alle fünf.
- **Teilmengen-Suche (FR-S3):** Suche „W" findet WU und WB, Suche „WU" findet WUB, aber nicht WB.
- **Selektionslogik:** Alle 31 Codes liefern eine gültige Seite; fehlender Content erzeugt keinen Fehler (FR-C11).
- **Ally/Enemy-Berechnung** gegen die tatsächliche Nachbarschaft im Rad.
- **Zugriffsschutz:** Ohne Gate-Cookie ist jede URL gesperrt; ohne Login sind Profile gesperrt; fremde Testhistorie ist nie sichtbar (FR-S1, FR-P6).
- **FR-P8:** Löschen des referenzierten Testergebnisses leert die Referenz, lässt die Farben aber stehen.

---

## 11. Deployment und Betrieb

### 11.1 Aufbau
`compose.yaml` mit `web`, `db`, `caddy`. Konfiguration ausschließlich über Umgebungsvariablen (`django-environ`), keine Secrets im Repository. Getrennte Settings-Module für Entwicklung und Produktion.

### 11.2 Ablauf eines Deployments
1. CI baut das Image und veröffentlicht es in der GitHub Container Registry.
2. Auf dem Server: `docker compose pull`
3. **Migrations als eigener Schritt:** `docker compose run --rm web python manage.py migrate`
4. `docker compose up -d`
5. Healthcheck `/healthz` prüft Datenbankverbindung und Migrationsstand.

Schritt 3 bleibt bewusst getrennt und läuft nicht beim Containerstart — sonst migrieren mehrere Worker gleichzeitig, und ein Fehlschlag zeigt sich erst im Log.

### 11.3 CI (GitHub Actions)
Ruff (Lint und Format) · `manage.py check --deploy` · pytest gegen ein Postgres-Service-Image · `makemigrations --check --dry-run` (fängt vergessene Migrationen) · Image-Build.

### 11.4 Backups
Ab v0.2, sobald echte Nutzerdaten entstehen: nächtlicher `pg_dump` in ein Volume, Aufbewahrung 14 Tage. **Eine Wiederherstellung wird einmal geprobt** — ein ungetestetes Backup ist keins.

---

## 12. Migrationspfad in die Cloud

Vorbereitet, nicht vorweggenommen:

- Anwendung ist zustandslos (Sessions in der Datenbank, generierte Avatare statt hochgeladener Dateien) → horizontal skalierbar ohne Umbau.
- Sämtliche Konfiguration über Umgebungsvariablen → kein Codeeingriff beim Umzug.
- Datenbank nur über `DATABASE_URL` angebunden → Wechsel auf eine verwaltete Postgres-Instanz ist eine Variablenänderung.
- Image liegt bereits in einer Registry → jeder Container-Dienst kann es ausführen.
- Übernimmt der Anbieter TLS, entfällt Caddy ersatzlos.

Der Umzug ist damit ein eigenständiger Lern-Task und kein Refactoring.

---

## 13. Bewusst nicht verwendet

| Verzichtet auf | Grund |
|---|---|
| React / Vue | §4 löst das Kernfeature ohne zweites Paradigma und ohne Node-Toolchain |
| Tailwind | Braucht einen Build-Schritt; zwei eigenständige Layouts sind mit Media Queries direkter |
| Django REST Framework | Es gibt keinen API-Konsumenten. Kommt, wenn er kommt |
| Redis | Sessions und Rate Limiting laufen in Postgres. Bei 3–10 Nutzenden wäre ein weiterer Dienst reine Betriebslast |
| Celery | Keine asynchronen Aufgaben im Scope |
| `django-allauth` | Kein Social Login, kein Mailversand (FR-U7). Djangos eigene Auth-Views reichen |
| Dateiupload / Objektspeicher | Avatare werden generiert (FR-P3) |
