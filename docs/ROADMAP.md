# Roadmap — Magic Personality

**Status:** Festgelegt · **Datum:** 2026-09-06
Grundlage: `docs/PRD.md`, `docs/ARCHITECTURE.md`, `docs/DECISIONS.md`

---

## Arbeitsweise

Jeder Task ist einzeln umsetzbar und einzeln überprüfbar. Reihenfolge innerhalb eines Meilensteins ist bindend, wo Abhängigkeiten genannt sind — sonst frei.

**Für jeden Task gilt (Definition of Done):**
- Tests für die fachliche Logik geschrieben und grün.
- `ruff check` und `ruff format --check` sauber.
- Migrationen im Repository, `makemigrations --check` meldet nichts Offenes.
- Nur das geändert, was der Task verlangt.
- Weicht die Umsetzung von `ARCHITECTURE.md` ab: **stoppen und rückfragen**, nicht die Architektur nebenbei ändern.
- Neue Entscheidungen als Eintrag in `DECISIONS.md`.

**Legende:** `FR-*` / `NFR-*` verweisen auf `PRD.md`, `D-*` auf `DECISIONS.md`.

---

# M0 · Fundament

Kein Nutzerwert, aber alles Folgende hängt daran. Bewusst klein gehalten.

#### 0.1 · Projektgerüst
**Ziel:** Lauffähiges Django-Projekt in der Struktur aus `ARCHITECTURE.md` §5.
**Abhängig von:** —
**Fertig, wenn:**
- [x] `config/settings/` in `base` / `dev` / `prod` getrennt, Konfiguration über Umgebungsvariablen (`django-environ`), keine Secrets im Repo.
- [x] Apps `core`, `colors`, `accounts`, `quiz`, `social` angelegt und registriert.
- [x] Ruff und pytest + pytest-django konfiguriert, ein Beispieltest läuft.
- [x] `.env.example` vorhanden, `.env` in `.gitignore`.
- [x] `python manage.py check` läuft fehlerfrei.

#### 0.2 · Eigenes User-Modell
**Ziel:** `AbstractBaseUser` mit E-Mail als Anmeldefeld, ohne `username`.
**Abhängig von:** 0.1 · **Anforderungen:** FR-U1, FR-U2, D-26
**Fertig, wenn:**
- [x] `accounts.User` mit `USERNAME_FIELD = "email"`, `PermissionsMixin`, eindeutiger E-Mail.
- [x] `AUTH_USER_MODEL` gesetzt, **bevor** die erste Migration erzeugt wird.
- [x] Argon2 als Passwort-Hasher aktiv.
- [x] `createsuperuser` funktioniert.

> Kritischer Task: Django lässt das User-Modell später nicht ohne Weiteres austauschen. Muss vor jeder anderen Migration erledigt sein.

#### 0.3 · Docker Compose lokal
**Ziel:** `docker compose up` startet Anwendung und Datenbank.
**Abhängig von:** 0.1 · **Anforderungen:** NFR-10
**Fertig, wenn:**
- [x] `Dockerfile` (Python 3.12, Gunicorn, WhiteNoise), `compose.yaml` mit `web` und `db` (PostgreSQL 16).
- [x] Datenbankanbindung ausschließlich über `DATABASE_URL`.
- [x] `/healthz` prüft Datenbankverbindung und Migrationsstand.
- [x] Compose-Healthcheck auf `/healthz`.

#### 0.4 · Basis-Layout und i18n
**Ziel:** Grundtemplate, CSS-Fundament, aktive Sprachauflösung.
**Abhängig von:** 0.1 · **Anforderungen:** NFR-4, NFR-6, D-15, D-25
**Fertig, wenn:**
- [x] Basis-Template mit Kopf-, Inhalts- und Fußbereich; HTMX eingebunden, CSRF-Token global über `hx-headers`.
- [x] CSS mit Custom Properties für Farben, Abstände, Typografie. Kein Build-Schritt, kein Node.
- [x] `LocaleMiddleware` aktiv, `locale/` angelegt, jeder Anzeigetext über `gettext`.
- [x] Ein Test stellt sicher, dass Templates keinen unübersetzten Anzeigetext enthalten (Stichprobe reicht).

#### 0.5 · Zugangssperre
**Ziel:** Ohne Invite-Code ist nichts erreichbar.
**Abhängig von:** 0.4 · **Anforderungen:** FR-A1 bis FR-A4, D-09
**Fertig, wenn:**
- [x] Middleware prüft ein signiertes Cookie; freigelistet sind nur Gate-View, `/healthz`, statische Dateien.
- [x] Code kommt aus einer Umgebungsvariable.
- [x] Rate Limiting auf der Code-Eingabe.
- [x] `X-Robots-Tag: noindex` als Header, dazu `robots.txt` mit `Disallow: /`.
- [x] Test: ohne Cookie ist **jede** URL gesperrt, auch unbekannte Pfade.

#### 0.6 · CI-Pipeline
**Ziel:** Jeder Push wird automatisch geprüft.
**Abhängig von:** 0.3 · **Anforderungen:** ARCHITECTURE §11.3
**Fertig, wenn:**
- [x] GitHub Actions: Ruff, `check --deploy`, pytest gegen ein Postgres-Service-Image, `makemigrations --check --dry-run`, Image-Build.
- [x] Image wird in die GitHub Container Registry veröffentlicht.
- [x] Ein absichtlich eingebauter Fehler lässt die Pipeline rot werden (einmal verifiziert, dann zurückgenommen).

---

# M1 · v0.1 — Color Infos

#### 1.1 · Datenmodell Farben
**Ziel:** Die Content-Entitäten aus PRD §6.1.
**Abhängig von:** 0.2 · **Anforderungen:** D-02, D-03, D-05, D-27
**Fertig, wenn:**
- [x] `Color`, `ColorCombination`, `Trait`, `CombinationTrait`, `Perspective` inklusive Migrationen.
- [x] `ColorCombination.code` ist der kanonisch sortierte WUBRG-Code, eindeutig je Locale.
- [x] `CombinationTrait.leaning_toward` verweist auf eine Farbe oder ist leer.
- [x] `Perspective.from_color` leer bedeutet neutrale Sicht.
- [x] Eine Datenmigration legt die fünf Farben und **alle 31 Kombinationen** an.
- [x] Test: es existieren genau 31 Kombinationen, alle Codes sind kanonisch sortiert.

#### 1.2 · Farbrad-Logik
**Ziel:** Nachbarschaft, Ally/Enemy und Geometrie an genau einer Stelle.
**Abhängig von:** 1.1 · **Anforderungen:** FR-C9, D-04
**Fertig, wenn:**
- [x] Eine Konstante beschreibt die Radposition; Nachbarschaft, Feindschaft und SVG-Koordinaten leiten sich daraus ab.
- [x] `ColorCombination.relation` liefert bei zwei Farben ALLY oder ENEMY, sonst nichts.
- [x] Tests gegen die tatsächlichen zehn Paare: fünf Ally, fünf Enemy.

#### 1.3 · Seed-Mechanismus
**Ziel:** Content aus versionierten Dateien einspielen.
**Abhängig von:** 1.1 · **Anforderungen:** D-28
**Fertig, wenn:**
- [x] JSON-Format unter `seeds/` dokumentiert (im Repo, nicht nur im Kopf).
- [x] `manage.py seed_content --locale en` ist **idempotent** — zweimaliger Lauf ändert nichts.
- [x] Unbekannte Felder oder unbekannte Farbcodes brechen mit klarer Fehlermeldung ab.
- [x] Test: Seed einspielen, zweiter Lauf erzeugt keine Änderung.

#### 1.4 · Content erfassen
**Ziel:** Die eigentlichen Inhalte aus der Quelle, paraphrasiert.
**Abhängig von:** 1.3 · **Anforderungen:** PRD §9, D-12
**Fertig, wenn:**
- [x] Für alle **fünf Einzelfarben**: Name, Ziel, Mittel, Guiding Question, Eigenschaften (center und zu beiden Nachbarn tendierend, je mit Typ).
- [x] Für alle **zehn Zweierkombinationen**: Name, Guiding Question, Archetype; bei Ally zusätzlich Eigenschaften.
- [x] Für alle **fünf Feindpaare**: je drei Perspektiven (A über B, B über A, neutral).
- [x] Für alle **zehn Zweierkombinationen** das Fünfeck-Wort (`theme`); je Perspektive die beiden kurzen Pol-Wörter an den Enden der Diagonale (D-37).
- [x] Für 3er-, 4er- und Fünffarb-Kombinationen: **nur der Name** (FR-C11, D-02).
- [x] Texte sind paraphrasiert, nicht wörtlich übernommen.
- [x] Die bestehende KI-generierte JSON-Datei wird ersetzt, nicht weiterverwendet.

> Größter inhaltlicher Einzelposten des Projekts. Nicht mit einem Coding-Task in derselben Sitzung vermischen.

#### 1.5 · Fünfeck darstellen
**Ziel:** Das Fünfeck als SVG, ohne Interaktion.
**Abhängig von:** 1.2, 0.4 · **Anforderungen:** FR-C1 bis FR-C3
**Fertig, wenn:**
- [x] Spitze oben, im Uhrzeigersinn White, Blue, Black, Red, Green.
- [x] Je Farbe Symbol im Kreis plus Name.
- [x] Koordinaten stammen aus der Konstante aus 1.2, nicht aus fest eingetragenen Werten.
- [x] Mana-Symbole eingebunden, Fan-Content-Hinweis im Footer.

#### 1.6 · Selektion und Routing
**Ziel:** Auswahl funktioniert vollständig **ohne** JavaScript.
**Abhängig von:** 1.5 · **Anforderungen:** FR-C4 bis FR-C7, D-24
**Fertig, wenn:**
- [x] `/colors/` und `/colors/<code>/` liefern jeden der 31 Codes gültig aus.
- [x] Jede Farbe ist ein Link auf die URL, die sich beim Umschalten dieser Farbe ergibt.
- [x] „Zurücksetzen" führt auf `/colors/`.
- [x] Nicht kanonische Codes (`/colors/uw/`) leiten dauerhaft auf die kanonische Form um.
- [x] Ungültige Codes ergeben 404.
- [x] Selektierte Farben sind hervorgehoben, nicht selektierte zurückgenommen.
- [x] Test: alle 31 Codes liefern Status 200.

#### 1.7 · Inhalte je Selektionsgröße
**Ziel:** Die Tabelle aus PRD §5.2 vollständig.
**Abhängig von:** 1.4, 1.6 · **Anforderungen:** FR-C8, FR-C10, FR-C11
**Fertig, wenn:**
- [x] **0 Farben:** Ally-Themen und neutrale Enemy-Pole am Fünfeck; Ziel/Mittel stehen stattdessen in der Info-Box bei 1 Farbe, damit das Fünfeck über alle Selektionsgrößen hinweg identisch bleibt (D-45).
- [x] **1 Farbe:** Name, Guiding Question, Eigenschaften (center und in einer Zeile nach links/rechts tendierend gruppiert); Allies/Enemies benannt statt Archetypen-Ausblick und Perspektiven-Text (D-40).
- [x] **2 Farben:** Beziehungstyp, Name, Guiding Question, Archetype; bei Ally Eigenschaften plus gemeinsamer Feind und Neighbour-Ally-Conflict (D-40), bei Enemy alle drei Perspektiven.
- [x] **3–5 Farben:** Name.
- [x] Die Linien am Fünfeck sind je Selektionszustand nach der Tabelle in PRD §5.2 beschriftet — einschließlich der Linien, die bewusst leer bleiben (D-37) und des Enemy-Themas auf der eigenen Diagonale (D-43).
- [x] Eigenschaftstyp wird **nicht allein farblich** unterschieden (Symbol oder Beschriftung, NFR-6).
- [x] Fehlender Content erzeugt einen leeren Bereich, keinen Fehler.
- [x] Test: eine 3er-Kombination ohne Content rendert fehlerfrei.

#### 1.8 · HTMX-Beschleunigung
**Ziel:** Selektion ohne vollen Seitenaufbau.
**Abhängig von:** 1.7 · **Anforderungen:** D-24
**Fertig, wenn:**
- [x] Klick tauscht nur das Info-Panel, `hx-push-url` aktualisiert die Adresse.
- [x] Vor- und Zurück-Navigation stellt den richtigen Zustand her.
- [x] Bei deaktiviertem JavaScript funktioniert weiterhin alles (nur als vollständiger Seitenaufruf).

#### 1.9 · Tastatur und Barrierefreiheit
**Ziel:** Bedienbar ohne Maus und mit Screenreader.
**Abhängig von:** 1.8 · **Anforderungen:** FR-C5, FR-C8, NFR-5, NFR-6
**Fertig, wenn:**
- [x] `W U B R G` schalten die jeweilige Farbe um, `Esc` setzt zurück.
- [x] Farben sind über Tab erreichbar, mit Enter und Leertaste bedienbar, sichtbar fokussiert.
- [x] `aria-pressed` spiegelt den Zustand.
- [x] Live-Region sagt nach dem Austausch den neuen Kombinationsnamen an.
- [x] Hervorhebung schaltet sofort um, bevor die Antwort eintrifft.
- [x] Eigenes JavaScript bleibt unter etwa 150 Zeilen und ohne Framework.

#### 1.10 · Mobiles Layout
**Ziel:** Eigenständige Gestaltung, keine skalierte Desktop-Ansicht.
**Abhängig von:** 1.9 · **Anforderungen:** NFR-3, D-14
**Fertig, wenn:**
- [x] Fünfeck oben, alle Informationen als zusammenhängender Block darunter.
- [x] Eigenschaften werden mobil **nicht** am Fünfeck verortet.
- [x] Bei 375 px Breite ohne horizontales Scrollen bedienbar; Trefferflächen ausreichend groß.

#### 1.11 · Rechtliches und About
**Ziel:** Pflichtangaben und Quellenkennzeichnung.
**Abhängig von:** 0.4 · **Anforderungen:** PRD §9, D-12
**Fertig, wenn:**
- [x] Footer: Quellenlink auf den Artikel. Der Fan-Content-Hinweis im vorgeschriebenen Wortlaut steht seit Task 1.5.
- [x] About-Seite mit Kontaktangabe.
- [x] Datenschutzseite als Platzhalter angelegt (Inhalt kommt mit 2.14, sobald personenbezogene Daten entstehen).

#### 1.12 · Erstes Deployment
**Ziel:** v0.1 läuft erreichbar auf dem kleinen Server.
**Abhängig von:** 1.10, 1.11, 0.6 · **Anforderungen:** NFR-10, D-29
**Fertig, wenn:**
- [x] Caddy als Reverse Proxy mit automatischem TLS.
- [x] Migrations laufen als **eigener Schritt**, nicht beim Containerstart.
- [x] Deployment-Ablauf in `docs/DEPLOYMENT.md` dokumentiert und einmal von Grund auf durchgespielt.
- [x] Zugangssperre greift auch in Produktion.
- [x] `/healthz` von außen erreichbar, alles andere gesperrt.

**Meilenstein v0.1 abgeschlossen, wenn** alle Abnahmekriterien aus PRD §11 (v0.1) erfüllt sind.

---

# M2 · v0.2 — Test und Profil

#### 2.1 · Profil-Datenmodell
**Abhängig von:** 0.2, 1.1 · **Anforderungen:** FR-P1 bis FR-P5, D-07, D-22, D-27
**Fertig, wenn:**
- [x] `Profile` mit `nickname`, `bio`, optionalem `user` (1:1).
- [x] Eindeutigkeit des Nicknames über einen funktionalen Index auf `Lower("nickname")`.
- [x] `ColorAssignment` mit `profile`, `author_profile`, Fremdschlüssel auf `ColorCombination`, `source`, optionaler Testreferenz.
- [x] Test: zwei Profile mit `Alice` und `alice` sind nicht gleichzeitig anlegbar.

> Umgesetzt nach Task 2.6, nicht davor — siehe D-54: `ColorAssignment.test_result` verweist auf `quiz.TestResult`, das sonst noch nicht existiert hätte.

#### 2.2 · Registrierung, Login, Logout
**Abhängig von:** 2.1, 0.5 · **Anforderungen:** FR-U1 bis FR-U6, D-08
**Fertig, wenn:**
- [x] Registrierung legt User und Profil gemeinsam an; Mindestlänge Passwort 10 Zeichen.
- [x] Sessions in der Datenbank, Cookie `httpOnly`, `Secure`, `SameSite=Lax`.
- [x] Passwortänderung beendet alle **anderen** Sessions.
- [x] Rate Limiting auf Login und Registrierung (`django-axes`).
- [x] Djangos Passwort-Reset-URLs sind **nicht** eingebunden (FR-U7).
- [x] Test: nach Passwortänderung ist eine zweite Session ungültig.

#### 2.3 · Account löschen
**Abhängig von:** 2.2 · **Anforderungen:** FR-U8
**Fertig, wenn:**
- [x] View mit ausdrücklicher Bestätigung.
- [x] Profil, Farbzuordnung, Testhistorie und Freundschaftsbeziehungen werden mitgelöscht.
- [x] Test: nach Löschung existiert keine Zeile mehr, die auf den Account verweist.

> Freundschaftsbeziehungen: `Friendship` existiert erst ab Task 3.4 und verweist dann per `on_delete=CASCADE` auf `Profile` — nichts, was hier schon zu tun wäre.

#### 2.4 · Profil ansehen und bearbeiten
**Abhängig von:** 2.2 · **Anforderungen:** FR-P1, FR-P4
**Fertig, wenn:**
- [x] Nickname, Bio und Farben (1 bis 5, frei wählbar) bearbeitbar.
- [x] Farbauswahl setzt `source = SELF_MANUAL` und leert die Testreferenz.
- [x] Serverseitige Validierung; Nickname-Kollision wird verständlich gemeldet.

#### 2.5 · Generiertes Profilbild
**Abhängig von:** 2.4 · **Anforderungen:** FR-P3, D-13
**Fertig, wenn:**
- [x] SVG wird deterministisch aus den hinterlegten Farben erzeugt, kein Upload, keine Dateiablage.
- [x] Profil ohne hinterlegte Farben erhält eine neutrale Darstellung.

#### 2.6 · Fragebogen-Datenmodell
**Abhängig von:** 1.1 · **Anforderungen:** FR-T1 bis FR-T6, D-16
**Fertig, wenn:**
- [x] `Questionnaire` mit Versionsnummer, `Question` mit `position` und `dimension`, `AnswerOption` mit Farbe.
- [x] `TestResult` mit `profile`, Fragebogenversion, Zeitpunkt, `scores` als JSON, Ergebnisfarben.
- [x] Seed-Command für Fragebögen; eine veröffentlichte Version ist unveränderlich.

> Umgesetzt vor Task 2.1, siehe D-54.

#### 2.7 · Die 30 Fragen schreiben
**Abhängig von:** 2.6 · **Anforderungen:** FR-T1 bis FR-T4, R-3, D-60
**Fertig, wenn:**
- [x] 30 Fragen mit je zwei Antworten in `seeds/questionnaire_v1.json`.
- [x] Jedes der zehn Farbpaare kommt **genau einmal je Dimension** (Handeln, Antrieb, Wahrnehmung) vor; jede Farbe erscheint in genau zwölf Fragen.
- [x] Jede Frage schildert eine Situation; die Farbzuordnung wird nicht benannt.
- [x] Qualitätsregeln aus D-60 eingehalten; automatisch prüfbare davon per Test abgesichert.
- [x] Automatischer Test prüft die Balance gegen die Seed-Datei.

> Umfang gegenüber der ursprünglichen Fassung (20 Fragen, vier Dimensionen) geändert, siehe D-60. Nach eigenem Testdurchlauf veröffentlicht (`"published": true`, 2026-09-17); Änderungen an den Fragen brauchen ab jetzt eine neue Version (FR-T6).

> Qualitätsentscheidender Task (R-3). Eigene Sitzung, nicht nebenbei.

#### 2.8 · Test durchführen
**Abhängig von:** 2.7 · **Anforderungen:** FR-T7 bis FR-T9
**Fertig, wenn:**
- [x] Freies Vor- und Zurückspringen vor der Abgabe, Antworten bleiben erhalten.
- [x] Abgabe erst möglich, wenn alle Fragen beantwortet sind; Fortschritt sichtbar.
- [x] Kein serverseitiger Zwischenstand.
- [x] Auch ohne Login durchführbar (Zugangssperre gilt trotzdem).

> Vor Task 2.7 umgesetzt (auf Wunsch): der Mechanismus kennt "20" nirgends fest verdrahtet, sondern verarbeitet immer *alle* Fragen der aktuell veröffentlichten Version — gegen einen frei erfundenen Dummy-Fragebogen getestet (`apps/quiz/tests/conftest.py`). Die Auswertungsregel selbst (FR-T10 bis FR-T12) ist bewusst nicht Teil dieses Tasks — die Ergebnisseite zeigt bis Task 2.9/2.10 nur die rohen Punkte je Farbe.

#### 2.9 · Auswertung
**Abhängig von:** 2.8 · **Anforderungen:** FR-T10 bis FR-T12, D-17
**Fertig, wenn:**
- [x] Regel exakt wie FR-T11 umgesetzt, `T` über Einstellung konfigurierbar (Standard 2).
- [x] Gleichstand an der Schnittgrenze nimmt alle betroffenen Farben auf.
- [x] Ergebnis wird auf eine der 31 Kombinationen abgebildet.
- [x] Tabellengetriebene Tests: klarer Dreier, deutlicher Zweier, deutlicher Vierer, Gleichstand an der Grenze, Gleichstand über alle fünf.

> Zwei von FR-T11/FR-T12 offengelassene Randfälle festgelegt, siehe D-59.

#### 2.10 · Ergebnis anzeigen und übernehmen
**Abhängig von:** 2.9, 2.4 · **Anforderungen:** FR-T13, FR-T14
**Fertig, wenn:**
- [x] Ergebnis zeigt Kombinationsnamen, Punkte aller fünf Farben und verlinkt auf `/colors/<code>/`.
- [x] Eingeloggt: Ergebnis landet automatisch in der Historie; Übernahme ins Profil wird **angeboten**, nicht erzwungen.
- [x] Übernahme setzt `source = SELF_TEST` und die Testreferenz.

> Übernahme liest die zum Testzeitpunkt gespeicherte Kombination (`TestResult.result_colors`), berechnet nicht neu — siehe D-61.

#### 2.11 · Ergebnis ohne Anmeldung
**Abhängig von:** 2.10 · **Anforderungen:** FR-T15, FR-T16, D-18
**Fertig, wenn:**
- [x] Ergebnis wird im `localStorage` zwischengespeichert, Registrierung wird angeboten.
- [x] Nach Registrierung **und** nach Login mit bestehendem Account wird es in die Historie übernommen und die Übernahme ins Profil angeboten.
- [x] Zwischenspeicher wird danach geleert.
- [x] Manipulierte oder veraltete Daten im Zwischenspeicher werden serverseitig abgewiesen, nicht übernommen.

> Signiertes Token (wie das Gate-Cookie) statt Klartext; globales Einlöse-Skript statt fester Zielseite nach Login/Registrierung — siehe D-62.

#### 2.12 · Testhistorie
**Abhängig von:** 2.10 · **Anforderungen:** FR-P6 bis FR-P8, FR-T17, D-19
**Fertig, wenn:**
- [x] Historie nur im eigenen Profil sichtbar, je Eintrag Datum, Punkte, Ergebnis.
- [x] Einzelne Einträge löschbar.
- [x] Löschen des referenzierten Eintrags leert die Referenz, lässt die Profilfarben aber bestehen.
- [x] Test: fremde Historie ist über keinen Pfad erreichbar.

> `on_delete=SET_NULL` (schon seit Task 2.1 auf `ColorAssignment.test_result`) erledigt FR-P8 automatisch — die View muss die Referenz nicht selbst leeren.

#### 2.13 · „Meine Farben auswählen"
**Abhängig von:** 2.4, 1.8 · **Anforderungen:** FR-C12
**Fertig, wenn:**
- [x] Button erscheint nur bei angemeldeten Nutzenden mit hinterlegten Farben und führt auf den passenden Code.

#### 2.14 · Datenschutz und Backups
**Abhängig von:** 2.3, 1.12 · **Anforderungen:** PRD §9, NFR-9, ARCHITECTURE §11.4
**Fertig, wenn:**
- [x] Datenschutzseite mit Inhalt: welche Daten, wo, wie lange, wie löschbar.
- [x] Nächtlicher `pg_dump`, Aufbewahrung 14 Tage.
- [x] **Eine Wiederherstellung wurde einmal erfolgreich durchgeführt** und dokumentiert.

> Backup als Docker-Volume über `scripts/backup.sh` + Cron (kein eigener vierter Container, ARCHITECTURE.md §2). Wiederherstellung lokal geprobt, Runbook in `docs/DEPLOYMENT.md` ("Backups"). Serverstandort (STRATO, Rechenzentrum innerhalb der EU) auf Rückfrage von der Nutzerin bestätigt.

#### 2.15 · Hauptnavigation
**Abhängig von:** 2.8, 1.6 · **Anforderungen:** FR-T7, NFR-3, NFR-5, NFR-6, D-64
**Fertig, wenn:**
- [x] Kopfbereich zeigt neben dem Projektnamen die Links „Colors“ (`/colors/`) und „Personality Test“ (`/quiz/`).
- [x] Der aktive Bereich ist mit `aria-current="page"` markiert und nicht nur farblich hervorgehoben.
- [x] Kein JavaScript nötig; bei 375 px Breite ohne horizontales Scrollen.
- [x] `seed_questionnaire` ist Teil des Deployment-Ablaufs in `docs/DEPLOYMENT.md`.

> Nachgetragen nach dem ersten Deployment von v0.2: Keine Aufgabe sah einen Einstieg in den Test vor, er war nur über die direkte URL erreichbar. Gleichzeitig fehlte `seed_questionnaire` im Deployment-Ablauf, `/quiz/` lieferte auf dem Server deshalb 404.

#### 2.16 · Fragebogen v2
**Abhängig von:** 2.7, 2.9 · **Anforderungen:** FR-T1 bis FR-T5, FR-T11, R-3, R-4, D-65
**Fertig, wenn:**
- [x] 15 Fragen mit je fünf Antworten (eine je Farbe) in `seeds/questionnaire_v2.json`, je 5 pro Dimension.
- [x] Testende wählen die beste und die zweitbeste Antwort; sie geben 2 bzw. 1 Punkt. Dieselbe Antwort auf beiden Plätzen wird abgewiesen.
- [x] Punkte je Rang und `T` stehen je Fragebogen-Version in der Seed-Datei; v1 funktioniert unverändert weiter.
- [x] Antworten erscheinen in der Reihenfolge der Seed-Datei, nicht nach Farbe sortiert.
- [x] `T` für v2 per Simulation eingestellt (D-65).
- [x] Qualitätsregeln aus D-65 eingehalten; automatisch prüfbare davon per Test gegen die Seed-Datei abgesichert.
- [x] Eigener Testdurchlauf, danach `"published": true` (2026-09-17).

> Nachgetragen nach dem eigenen Durchlauf von v1: Das Ergebnis war zu ausgeglichen, weil bei zwei Antworten auch Farben Punkte bekommen, die man nicht hat (D-65).

**Meilenstein v0.2 abgeschlossen** — alle Abnahmekriterien aus PRD §11 (v0.2) sind erfüllt.

---

# M3 · v1.0 — Social

#### 3.1 · Fremde Profile
**Abhängig von:** 2.4 · **Anforderungen:** FR-S1, D-19
**Fertig, wenn:**
- [x] `/u/<nickname>/` zeigt Nickname, Bild, Bio, Farben — **nicht** Historie, **nicht** E-Mail.
- [x] Nur für Angemeldete erreichbar.
- [x] Test: Nicht-Angemeldete werden abgewiesen; Historie taucht in keiner Antwort auf.

#### 3.2 · Suche nach Nickname
**Abhängig von:** 3.1 · **Anforderungen:** FR-S2
**Fertig, wenn:**
- [x] Teilstring-Suche, Groß- und Kleinschreibung egal, Treffer verlinken auf das Profil.

#### 3.3 · Suche nach Farbkombination
**Abhängig von:** 3.2 · **Anforderungen:** FR-S3, D-21, D-27
**Fertig, wenn:**
- [x] Ergebnis sind alle Profile, deren Kombination die gesuchte **enthält**.
- [x] Test: Suche „W" findet WU und WB; Suche „WU" findet WUB, aber nicht WB.
- [x] Auswahl der Suchfarben nutzt dieselbe Darstellung wie das Fünfeck.

> Umsetzung siehe D-66: gleiche Geometrie/CSS-Klassen wie `apps.colors`, eigene schlanke Klasse statt Import aus dessen `views.py`.

#### 3.4 · Freundschaften
**Abhängig von:** 3.1 · **Anforderungen:** FR-S4, D-20, D-22
**Fertig, wenn:**
- [x] `Friendship` auf `Profile` (nicht auf `User`), Status PENDING oder ACCEPTED, mit Angabe wer angefragt hat.
- [x] Constraint verhindert doppelte Paarungen in beiden Richtungen und Selbstfreundschaft.
- [x] Anfrage senden, annehmen, ablehnen, bestehende Freundschaft auflösen.
- [x] Offene Anfragen sind im eigenen Profil sichtbar.
- [x] Test: Anfrage kann nicht doppelt gestellt und nicht von Dritten angenommen werden.

> Umsetzung siehe D-67: ein Datensatz je Paar in kanonischer Reihenfolge (statt fester Sender-/Empfänger-Rollen), Constraint deckt Duplikate und Selbstfreundschaft in einer Prüfung ab.

#### 3.5 · Freundeslisten und Graph
**Abhängig von:** 3.4 · **Anforderungen:** FR-S5, FR-S6
**Fertig, wenn:**
- [x] Eigene Freundesliste im eigenen Profil.
- [x] Freundesliste fremder Profile einsehbar und navigierbar.
- [x] Über mindestens zwei Ebenen durchklickbar, ohne Sackgasse.

#### 3.6 · Release-Durchsicht v1.0
**Abhängig von:** 3.5 · **Anforderungen:** PRD §11 (v1.0)
**Fertig, wenn:**
- [x] Alle Abnahmekriterien aus PRD §11 durchgegangen und abgehakt.
- [x] Zugriffsschutz durchgeprüft: Gate, Login-Pflicht, private Historie.
- [x] Prüfung gegen `ARCHITECTURE.md`: keine unbeabsichtigten Abweichungen.
- [x] Backup-Wiederherstellung erneut geprobt.
- [x] `DECISIONS.md` ist vollständig.

> **Abnahmekriterien PRD §11 (v1.0):**
> - „Fremde Profile sind nur eingeloggt sichtbar und zeigen keine Historie." — `apps.social.views.profile_detail` (`@login_required`), Testhistorie/E-Mail nirgends im Kontext/Template (Task 3.1, `apps/social/tests/test_profile_detail.py`).
> - „Beide Suchen liefern korrekte Ergebnisse, insbesondere die Teilmengen-Logik aus FR-S3." — Nickname-Suche (Task 3.2) und Farbsuche (Task 3.3) je mit eigener Testdatei; die DoD-Beispiele aus FR-S3 („W" findet WU/WB, „WU" findet WUB nicht WB) stehen wörtlich in `test_search_colors.py`.
> - „Freundschaftsanfragen lassen sich senden, annehmen, ablehnen und auflösen." — Task 3.4, `apps/social/friendships.py` plus `test_friendships.py` (Modell-Constraints, Logik, Views einzeln).
> - „Über Freundeslisten ist der Graph navigierbar." — Task 3.5, `test_friend_lists.py` inklusive eines Tests, der zwei Ebenen ohne Sackgasse durchklickt.
>
> Alle vier zusätzlich per komplettem Testlauf abgesichert (593 Tests, siehe unten) — nicht nur einzeln gelesen.
>
> **Zugriffsschutz:** `GateMiddleware` unterscheidet nicht nach Pfad (Task 0.5) — neu hinzugekommen ist ein expliziter Test für die v1.0-URLs selbst (`apps/core/tests/test_gate.py::test_social_urls_without_cookie_redirect_to_the_gate`), statt sich nur auf die allgemeine Regel zu verlassen. Login-Pflicht: jede Social-View trägt `@login_required` (`profile_detail`, `search`, `search_by_colors`, `send_friend_request`, `accept_friend_request`, `decline_friend_request`, `remove_friendship`). Private Historie: `TestResult` wird ausschließlich über `profile__user=request.user` gelesen (`apps/accounts/views.py`, `apps/quiz/views.py`), an keiner Stelle in `apps.social`.
>
> **Prüfung gegen `ARCHITECTURE.md`:** M3-Diff bleibt vollständig innerhalb von `apps/social` (plus kleine Ergänzungen in `apps/accounts/views.py`, `config/urls.py`, Templates) — Projektstruktur aus §5 unverändert eingehalten. Keine neuen Abhängigkeiten (`requirements/`, `compose*.yaml`, `Dockerfile`, `static/js/` unverändert seit v0.2). `Friendship` verweist auf `Profile`, nicht `User` (§6.1/D-22). Alle sichtbaren Texte laufen durch `gettext` (NFR-4, stichprobenartig per Grep über `templates/social/*.html` und den diff-Teil von `templates/accounts/profile.html` geprüft — keine hart codierten Strings). Mobil-Layout bei 375 px ohne horizontales Scrollen geprüft (NFR-3, `/search/colors/`, `/accounts/profile/`, `/u/<nickname>/`).
>
> **Backup-Wiederherstellung:** erneut geprobt (siehe `docs/DEPLOYMENT.md`, Abschnitt „Backups") — diesmal ausdrücklich mit der seit Task 3.4 neuen `social_friendship`-Tabelle: Dump erstellt, in eine Wegwerf-Datenbank eingespielt, Zeilenzahlen und alle drei DB-Constraints aus `Friendship.Meta` (D-67) nach der Wiederherstellung unverändert vorgefunden.
>
> **`DECISIONS.md`:** 67 Einträge (D-01 bis D-67), lückenlos durchnummeriert, keiner mit Status „Offen".

**Meilenstein v1.0 abgeschlossen** — das Produkt gilt als fertig.

---

# M4 · v1.2 — Profil-Überarbeitung

Anlass: Die Nutzung von v1.0/v1.1 hat gezeigt, dass das Profil mit einem einzigen „Speichern"-Knopf für alle Angaben fehleranfällig ist (unveränderte Farben wurden überschrieben, siehe D-72), und dass der Platz auf der Seite später Blogbeiträgen und Kommentaren zu Farben gehören soll (PRD §8.2). Gestaltung und Begründung: D-73. Anforderungen: PRD §5.5.1 (FR-P9 bis FR-P16). Jeder Task lässt die Anwendung lauffähig; die Reihenfolge ist bindend, wo Abhängigkeiten genannt sind.

#### 4.1 · Eine Profilseite für eigene und fremde Ansicht
**Abhängig von:** 3.5 · **Anforderungen:** FR-P9, D-73
**Fertig, wenn:**
- [x] `/u/<nickname>/` zeigt die eigene Person genauso wie fremde Profile; der bisherige Sonderfall-Redirect in `profile_detail` entfällt.
- [x] `/accounts/profile/` und alle Redirects darauf (Login, Speichern, Löschen) führen auf `/u/<eigener-nickname>/`; der Link im Kopfbereich ebenso.
- [x] Die Seite kennt den Betrachter (`is_owner`) und blendet Bearbeiten-Knöpfe, Anfragen und private Bereiche nur für die eigene Person ein.
- [x] Bestehende Funktionen bleiben erhalten (Bio, Farben mit Punkten, Freunde, Freundschaftsaktionen, Historie, Anfragen) — zunächst im heutigen Aussehen, noch ohne Redesign.
- [x] Test: eigenes Profil unter der neuen URL zeigt Bearbeiten-Zugänge, fremdes nicht; alte URL leitet weiter.

> Ein Profil ohne Nickname-Änderung im Weg: Ändert jemand den Nickname, führen alle Weiterleitungen auf die neue URL. Ein `createsuperuser`-Account ohne Profil ergibt weiterhin eine klare 404.

> Umsetzung: gemeinsamer Kontext in `apps/social/profile_page.py`, `Profile.get_absolute_url()` als einzige Quelle der Profil-Adresse. `/accounts/profile/` bleibt nur als Speichern-Endpunkt (POST) des Sammelformulars bis Task 4.5. Dabei ergänzt: Nicknames mit „/" oder nur aus Punkten werden abgewiesen, weil der Nickname jetzt in jeder Seite als Adresse im Kopfbereich steht und sonst ein Reverse-Fehler alle Seiten der Person zum Absturz brächte.

#### 4.2 · Kopfbereich mit Farbbanner und Freundschaftsaktion
**Abhängig von:** 4.1 · **Anforderungen:** FR-P10, NFR-5, NFR-6, D-73
**Fertig, wenn:**
- [x] Banner aus gleichbreiten Streifen der Profilfarben in WUBRG-Reihenfolge (1 bis 5); ohne Farben neutral. Umsetzung wie das Profilbild (`border-radius`/Streifen, keine SVG-`clipPath`, D-57), Farben nur über CSS-Eigenschaft je Streifen.
- [x] Profilbild überlappt das Banner; Nickname, Kombinationsname (verlinkt auf `/colors/<code>/`) und Bio-Zeile stehen auf der Seitenfläche, nie auf den Bannerfarben (Kontrast unabhängig von der Farbwahl).
- [x] Die Freundschaftsaktion (Anfrage senden, zurückziehen, annehmen/ablehnen, Freund entfernen) sitzt im Kopf und nutzt unverändert die POST-Endpunkte aus Task 3.4.
- [x] Beim eigenen Profil steht statt der Aktion ein Hinweis „you".
- [x] Test: alle vier Beziehungszustände zeigen die richtige Aktion; ein Profil ohne Farben rendert das neutrale Banner.

> Umsetzung: `templates/social/_profile_header.html` (Banner, Profilbild, Name, Kombination, Bio-Zeile auf 140 Zeichen gekürzt) und `_friend_action.html` (aus `profile_detail.html` in den Kopf verschoben). Das Banner sind `div`-Streifen mit `--segment-color`, dieselben `segments` wie beim Profilbild. Die Bereiche „Colors" und „Friends" weiter unten bleiben bis 4.7 bzw. 4.3 unverändert. Im Browser bei 1024 px und 375 px geprüft (kein horizontales Scrollen, Aktion umbricht unter den Namen).

#### 4.3 · Tabs und Freunde-Tab
**Abhängig von:** 4.2 · **Anforderungen:** FR-P11, FR-S5, FR-S6, D-73
**Fertig, wenn:**
- [x] Tabs sind echte Links auf eigene URLs (`/u/<nickname>/` = Pinnwand als Standardtab, `/u/<nickname>/friends/`), aktiver Tab mit `aria-current="page"` und nicht nur farblich markiert; kein JavaScript nötig.
- [x] Der Freunde-Tab zeigt die vollständige Freundesliste, bei der eigenen Person zusätzlich offene Anfragen (empfangen und gesendet) samt Annehmen/Ablehnen/Zurückziehen; ein Hinweis am Tab zeigt die Zahl neuer Anfragen.
- [x] Die Freundesliste bleibt über beliebig viele Ebenen durchklickbar (Task 3.5-DoD gilt weiter).
- [x] Bisherige Anfragen-Box im Profil entfällt zugunsten des Tabs.
- [x] Die Tab-Leiste enthält von Anfang an **Pinnwand** (Standard) und **Friends**; die Pinnwand zeigt bis zu ihrer Umsetzung einen „Coming soon"-Platzhalter (Task 4.7).
- [x] Test: fremde offene Anfragen tauchen nirgends in einem fremden Profil auf.

> Umsetzung: `profile_base.html` (Kopf + Tab-Leiste) als Grundgerüst, `profile_detail.html` = Tab Pinboard, `profile_friends.html` = Tab Friends unter `/u/<nickname>/friends/`. Der Kontext ist nach Tab geteilt (`profile_page.profile_context(tab=…)`). Bis 4.7 stehen auf dem Pinboard-Tab vorläufig noch Formular, Farben und das Private der eigenen Person unter dem Coming-soon-Platzhalter. Anfragen annehmen/ablehnen leitet weiterhin auf das Profil der anderen Person, nicht zurück auf den Friends-Tab. Im Browser bei 1024 und 375 px geprüft.

#### 4.4 · Private Tabs: Testhistorie und Einstellungen
**Abhängig von:** 4.3 · **Anforderungen:** FR-P6, FR-P7, FR-P11, FR-U8, D-19, D-73
**Fertig, wenn:**
- [x] `/u/<eigener-nickname>/history/` zeigt die bisherige Testhistorie samt „Use for profile" und Löschen; `/u/<eigener-nickname>/settings/` bündelt Passwort ändern und Account löschen.
- [x] Beide URLs sind für Gäste hinter dem Login. Ruft eine **andere** Person sie auf (`/u/person_b/history/` als nicht person_b), **leitet die Seite auf `/u/person_b/` weiter** (302, der Ausgang hängt vom Betrachter ab) — kein 404 und kein 403. Existiert die Person nicht, bleibt es bei 404.
- [x] Die Tabs erscheinen nur für die eigene Person.
- [x] Test: fremde Historie und fremde Einstellungen sind über keinen Pfad erreichbar; die Weiterleitung enthält keinen Inhalt der privaten Seite (ausdrücklich für die neuen URLs).

> Weiterleiten statt 404: Die Adresse verrät nichts, was nicht ohnehin öffentlich wäre — das Profil ist für jede angemeldete Person sichtbar, und die privaten Tabs gibt es bei jedem Profil gleichermaßen. Dieselbe Regel gilt für die Bearbeiten-Adressen (4.5, 4.6) und ist als Hilfsfunktion/Decorator für alle „nur eigene Person"-Seiten gedacht, damit sie nicht je Seite neu entschieden wird.

> Umsetzung: `apps/social/decorators.py:owner_only` trifft die Entscheidung (Gäste → Login, unbekannter Nickname → 404, andere Person → 302 auf `/u/<nickname>/` ohne Inhalt, auch bei POST) und reicht der View das Profil statt des Nicknames; Tasks 4.5 und 4.6 nutzen ihn für die Bearbeiten-Adressen. Die Einstellungen verlinken die bestehenden Seiten „Passwort ändern" (bisher nirgends in der Oberfläche verlinkt) und „Account löschen". Historie löschen führt zurück auf den History-Tab, Übernehmen auf das Profil (dort erscheinen die Punkte).

#### 4.5 · Nickname und Bio einzeln bearbeiten
**Abhängig von:** 4.1 · **Anforderungen:** FR-P12, FR-P2, D-72, D-73
**Fertig, wenn:**
- [x] Nickname und Bio haben je ein eigenes Formular und eigenen POST-Endpunkt; jeder speichert ausschließlich sein Feld.
- [x] Ohne JavaScript öffnet „Edit" eine eigene Seite mit nur diesem Formular; mit HTMX tauscht sich der Bereich an Ort und Stelle aus (D-24: Progressive Enhancement, der Zustand steht in der URL).
- [x] Serverseitige Validierung; Nickname-Kollision wird verständlich gemeldet, Abbrechen verwirft ohne Änderung.
- [x] Nach Nickname-Änderung führen Redirect und Links auf die neue URL.
- [x] Der bisherige Sammel-`ProfileForm` verliert Nickname und Bio.
- [x] Bearbeiten-Adressen einer anderen Person (GET und POST) leiten auf deren Profil weiter und ändern nichts (Regel aus 4.4).
- [x] Test: Speichern der Bio ändert weder Nickname noch Farben; Speichern des Nicknames ändert weder Bio noch Farben; ein POST auf die Bearbeiten-Adresse einer anderen Person verändert nichts.

> Umsetzung: Endpunkte `/u/<nickname>/edit/nickname/` und `/edit/bio/` (beide `owner_only`, GET und POST), Formulare `NicknameForm`, `BioForm` und — als Rest des früheren `ProfileForm` — `ColorsForm` in `apps/accounts/forms.py`. Die Bearbeiten-Adresse rendert dieselbe Profilseite mit **einem** Bereich im Bearbeiten-Modus (`editing`); mit HTMX holt sich der Link per `hx-select` genau diesen Bereich (`#profile-name`, `#profile-bio`) daraus, ohne JavaScript ist es die volle Seite. Bio-Speichern tauscht zusätzlich die Kurzfassung im Kopf mit (`hx-select-oob`, sonst bliebe sie veraltet). Der Nickname-Speichern ist bewusst ein normales POST, weil sich dabei Adresse und Kopf ändern. `/accounts/profile/` speichert nur noch die Farben, bis Task 4.6 sie ersetzt. Im Browser durchgespielt: Bio inline, vergebener Nickname (Fehler im Formular, nichts geändert), Umbenennen (Adresse, Kopfzeilen-Link und Tabs folgen).

#### 4.6 · Farben bearbeiten: Testergebnis übernehmen oder am Fünfeck wählen
**Abhängig von:** 4.5, 1.9 · **Anforderungen:** FR-P13, FR-P4, FR-P5, FR-P8, D-56, D-72
**Fertig, wenn:**
- [x] Eigenes Formular mit zwei Wegen: ein Testergebnis aus der Historie wählen (Radio je Eintrag mit Datum, Punkten, Kombination) oder manuell 1 bis 5 Farben wählen.
- [x] Testergebnis wählen setzt `source = SELF_TEST` und die Testreferenz (wie `adopt_result`); manuelle Wahl setzt `SELF_MANUAL` und leert die Referenz **nur bei tatsächlicher Änderung** (D-72).
- [x] Manuelle Wahl am Fünfeck mit derselben Geometrie/Darstellung wie in `apps.colors` und der Suche (D-66). Ohne JavaScript bleiben fünf Kontrollkästchen, mit JavaScript schaltet das Fünfeck die Kästchen; eigenes Skript klein, kein Framework (ARCHITECTURE.md §4.3).
- [x] Ohne Farben speichern entfernt die Zuordnung (wie bisher).
- [x] Neue Entscheidung ersetzt D-56 (Status *Ersetzt*), Begründung: die Bereiche sind jetzt getrennte Formulare, das ursprüngliche Gegenargument (mehrere Felder in einem POST) entfällt.
- [x] Test: Testergebnis wählen setzt Referenz und Punkte erscheinen im fremden Profil; unveränderte manuelle Wahl lässt die Referenz stehen; Bio/Nickname-Speichern fasst die Farben nie an.

> Umsetzung siehe D-74 (ersetzt D-56). Endpunkt `/u/<nickname>/edit/colors/` (`owner_only`), `ColorsForm` mit `choice` (Testergebnis-Primärschlüssel oder „manual") und `colors`; gemeinsame Übernahme-Funktion `apps/accounts/color_assignments.py:adopt_test_result` für Ergebnisseite, Historie und Formular. Fünfeck-Feld in `templates/social/_color_field.html` (Geometrie aus `apps.colors.pentagon`, Ecken als `role="checkbox"`), `static/js/profile_colors.js` 50 Zeilen. Im Browser mit JavaScript geprüft (Fünfeck statt Kästchen, Mausklick und Leertaste, beide Wege speichern, Kopf und Banner ziehen mit) und ohne (Klasse `js` entfernt: Kästchen sichtbar, Fünfeck versteckt). Speichern ist bewusst ein normales POST, weil sich der Kopf ändert.

#### 4.7 · Pinnwand-Platzhalter und Sidebar
**Abhängig von:** 4.3 · **Anforderungen:** FR-P14, D-70, NFR-6
**Fertig, wenn:**
- [x] Sidebar mit Karten: Bio, Farben (Kombinationsname verlinkt auf die Colors, bei übernommenem Testergebnis die Punkte je Farbe als Balken mit Buchstabe **und** Zahl, D-70) und Freundesvorschau (höchstens 8, Link auf den Freunde-Tab).
- [x] Bei der eigenen Person tragen Bio und Farben je einen „Edit"-Link auf ihre Bearbeiten-Seite (4.5/4.6) und einen Hinweis, wenn die Farben aus dem Test stammen.
- [x] Hauptbereich ist der Tab **Pinnwand** mit einem „Coming soon"-Platzhalter (fremd und eigen; kurzer Satz, was dort einmal steht: Favoriten, eigene oder fremde Beiträge und Kommentare). Keine Knöpfe oder Links ohne Ziel.
- [x] Die Idee ist vermerkt: PRD §8.2 (Pinnwand), D-73 und der Abschnitt „Nicht in dieser Roadmap" halten fest, dass Pinnwand-Einträge auf Beiträge/Kommentare beliebiger Autorschaft verweisen.
- [x] Fehlender Inhalt erzeugt leere Karten mit Hinweis, keinen Fehler (wie FR-C11).
- [x] Test: alle Kartenzustände (mit/ohne Farben, mit/ohne Testverknüpfung, mit/ohne Freunde) rendern fehlerfrei; die Pinnwand zeigt den Platzhalter.

> Umsetzung: `profile_detail.html` = Hauptbereich (Pinnwand-Platzhalter) plus `<aside>` mit den Karten `_card_bio.html`, `_card_colors.html` und `_card_friends.html`; die Sidebar steht im DOM hinter dem Hauptbereich und landet mobil darunter, sie gibt es nur im Pinboard-Tab. Die Punkte kommen als Balken mit Buchstabe **und** Zahl (`profile_page.score_bars`, Länge relativ zum höchsten Wert, Balkenfarbe wie der Halo der Ecke, weil Weiß als `Color.hex` kaum zu sehen wäre, D-42). Die Freundesvorschau zeigt höchstens acht Einträge (`FRIENDS_PREVIEW_LIMIT`) als einfache Liste, Task 4.8 ersetzt sie durch die Autorenkarte. Beim Bearbeiten der Farben wird die Sidebar per `:has()` breiter, damit das Fünfeck genug Trefferfläche hat (ohne `:has()` bleibt es funktionsfähig, nur schmaler). Im Browser bei 1024 und 375 px geprüft: eigenes und fremdes Profil, Bearbeiten in der Sidebar, kein horizontales Scrollen.

#### 4.8 · Autorenkarte als Komponente
**Abhängig von:** 4.2 · **Anforderungen:** FR-P15, D-57
**Fertig, wenn:**
- [x] `templates/social/_author_card.html`: Profilbild (bestehender `_avatar.html`), Nickname als Link, Kombinationsname als Chip; Größenvarianten klein und mittel.
- [x] Freundesliste (Tab und Vorschau) und beide Suchen nutzen die Komponente statt eigener Listen-Markup.
- [x] Mehrere Karten auf einer Seite erzeugen kein doppeltes `id` (D-57).
- [x] Die Komponente ist so gebaut, dass Beiträge und Kommentare sie später ohne Änderung einbinden (nur Profil als Kontext, keine Sonderfälle).
- [x] Test: Karte rendert mit und ohne Farben; Suchergebnisse und Freundesliste zeigen sie.

> Umsetzung: Inklusions-Tag `{% author_card profile size="small|medium" %}` (`apps/social/templatetags/social_tags.py`, Template `_author_card.html`) — braucht nur ein Profil, keine Sonderfälle je Einsatzort. Eingesetzt in der Freundesliste (medium), der Freundesvorschau der Sidebar und den offenen Anfragen (small) sowie in beiden Suchen (medium). Das Profilbild ist in der Karte Dekoration (`aria-hidden`), die Kombination steht als Text im Chip. Listen holen Zuordnung und Kombination per Prefetch (`friendships.prefetch_for_cards`), die fünf Farbwerte lädt das Tag einmal je Rendering: zusätzliche Karten kosten keine zusätzlichen Abfragen (per Test abgesichert). Dafür bekam `avatar.segments()` einen optionalen Parameter `hex_by_code`. Im Browser geprüft: Friends-Tab, Nickname- und Farbsuche, keine doppelten ids.

#### 4.9 · Mobiles Layout und Barrierefreiheit
**Abhängig von:** 4.7, 4.8 · **Anforderungen:** FR-P16, NFR-3, NFR-5, NFR-6
**Fertig, wenn:**
- [x] Bei 375 px: Banner und Kopf gestapelt, Tabs umbrechen, Sidebar-Karten unter dem Hauptbereich, kein horizontales Scrollen, Trefferflächen ausreichend groß.
- [x] Tastatur: alle Tabs, Edit-Links und Freundschaftsaktionen erreichbar und sichtbar fokussiert; Bearbeiten-Bereiche setzen den Fokus sinnvoll.
- [x] Bereichsüberschriften und Landmarks für Screenreader (`aria-labelledby` an den Karten); Tabs als Navigation mit `aria-current`, nicht als ARIA-Tabs-Widget.
- [x] Nach HTMX-Austausch eines Bereichs wird die Änderung angesagt (Live-Region, wie Task 1.9).
- [x] Eigenes Skript für Fünfeck-Formularfeld und Bereichsaustausch bleibt klein und ohne Framework.

> Umsetzung und Prüfung (im Browser bei 375 px, alle Profilseiten samt Bearbeiten-Ansichten und beide Suchen): kein horizontales Scrollen, keine Bedienelemente unter 44 px Höhe mehr — dafür bekamen Tabs, Bearbeiten-Links, Kombinations-Links, Autorenkarten, Einstellungs-Links, Schaltflächen und Eingabefelder `min-height: 2.75rem` (Hilfsklasse `.tap-target`). Die Testhistorie-Tabelle stapelt mobil zu Zeilen mit `data-label`. Tastatur: alle Tabs, Links, Schaltflächen und die Fünfeck-Ecken sind erreichbar und über `:focus-visible` sichtbar fokussiert; nach dem Öffnen eines Bereichs steht der Fokus im ersten Feld (`autofocus`), nach Speichern oder Abbrechen springt er auf den „Edit"-Link zurück (`static/js/profile_sections.js`, 32 Zeilen). Screenreader: Karten, Historie und Anfragen tragen `aria-labelledby`, die Sidebar ist ein beschriftetes `<aside>`, die Tabs eine beschriftete Navigation mit `aria-current` (kein ARIA-Tabs-Widget), Balken nennen die Farbe, Historie-Schaltflächen nennen das Ergebnis (`aria-label`). Die Live-Region `#profile-live-region` steht außerhalb der ausgetauschten Bereiche und sagt „Editing. The form is open.", „Saved." bzw. „Editing cancelled." an (im Browser mit `Saved.` und Fokus auf dem Edit-Link nachgewiesen). Eigenes JavaScript zusammen unter 320 Zeilen, ohne Framework (per Test abgesichert).

#### 4.10 · Release-Durchsicht v1.2
**Abhängig von:** 4.9 · **Anforderungen:** PRD §11 (v1.2)
**Fertig, wenn:**
- [x] Alle Abnahmekriterien aus PRD §11 (v1.2) durchgegangen und abgehakt.
- [x] Zugriffsschutz erneut geprüft: Gate, Login-Pflicht, private und Bearbeiten-Adressen leiten andere auf das öffentliche Profil weiter, Historie nirgends fremd sichtbar (ausdrücklich für alle neuen URLs).
- [x] Prüfung gegen `ARCHITECTURE.md`: keine unbeabsichtigten Abweichungen (JavaScript-Umfang, keine neuen Abhängigkeiten).
- [x] Bestehende Nutzerdaten unverändert: Zuordnungen, Testreferenzen und Freundschaften eines Datenbank-Dumps vor und nach dem Deployment stichprobenartig verglichen.
- [x] Backup-Wiederherstellung erneut geprobt.
- [x] `DECISIONS.md` ist vollständig, D-56 als ersetzt markiert.

> **Abnahmekriterien PRD §11 (v1.2):**
> - „Eigenes und fremdes Profil sind dieselbe Seite; private Bereiche sind für andere auf keinem Pfad erreichbar, ihre Adressen leiten auf das öffentliche Profil weiter." — Task 4.1/4.4, `test_profile_page.py`, `test_private_tabs.py` und die Matrix in `test_access_control.py`.
> - „Nickname, Bio und Farben lassen sich einzeln bearbeiten; das Speichern eines Bereichs verändert nie einen anderen, insbesondere nie die Testverknüpfung." — Task 4.5/4.6, `test_profile_sections.py`, `test_profile_colors.py`, `test_profile_edit.py` (D-72).
> - „Farben sind aus einem Testergebnis oder manuell am Fünfeck wählbar, mit und ohne JavaScript." — Task 4.6, im Browser mit JavaScript (Fünfeck, Maus, Leertaste) und ohne (Klasse `js` entfernt: Kästchen) nachgewiesen.
> - „Banner, Tabs und Sidebar funktionieren mit Tastatur und Screenreader und bei 375 px ohne horizontales Scrollen." — Task 4.2/4.3/4.7/4.9, im Browser über zehn Seiten bei 375 px gemessen (kein Überlauf, keine Bedienelemente unter 44 px), Struktur und Ansagetexte per `test_profile_accessibility.py`. Nicht abgedeckt: ein Durchlauf mit einem echten Screenreader (VoiceOver/NVDA).
> - „Die Autorenkarte erscheint in Freundeslisten und Suchergebnissen." — Task 4.8, `test_author_card.py`.
>
> **Zugriffsschutz:** Neue Matrix `apps/social/tests/test_access_control.py` läuft über **alle** Adressmuster der Social-App: ohne Gate-Cookie überall Weiterleitung zum Gate, ohne Anmeldung überall zum Login (GET und POST), für Testhistorie, Einstellungen und alle drei Bearbeiten-Adressen leitet jede andere Person (GET und POST) leer auf das öffentliche Profil weiter, die eigene Person erreicht sie, ein unbekannter Nickname liefert 404. Ein Test lädt sämtliche Adressen eines fremden Profils (samt Suche und Listen) und weist nach, dass nicht übernommene Historieneinträge nirgends vorkommen; fremde Historieneinträge lassen sich weder löschen noch übernehmen. Ein neu hinzugefügtes Adressmuster ohne Zuordnung in der Matrix lässt einen Test fehlschlagen.
>
> **Gegen `ARCHITECTURE.md`:** keine Migrationen, keine neuen Abhängigkeiten, `compose*.yaml`/`Dockerfile`/`Caddyfile` unverändert (`git diff main` leer). Bewusste, dokumentierte Erweiterungen: rund 280 Zeilen eigenes JavaScript in fünf kleinen Skripten (davon 83 neu in v1.2, ohne Framework, jede Funktion auch ohne Skript nutzbar; jetzt in §4.3.1 festgehalten und per Test begrenzt), der Decorator `owner_only` (neue Zeile in §7) und die Projektstruktur (§5). Das Fünfeck-Formularfeld weicht von D-56 ab und ist als D-74 dokumentiert.
>
> **Bestandsdaten:** Ohne Migrationen bleibt das Schema unverändert. Zusätzlich ein Vorher-nachher-Vergleich: Datensatz mit übernommenem Testergebnis, manueller Farbwahl, gelöschter Referenz, Profil ohne Farben, angenommenen und offenen Freundschaften; alle Tabellen (`accounts_profile`, `accounts_colorassignment`, `quiz_testresult`, `social_friendship`, `accounts_user` ohne `last_login`) vor und nach **196 Anfragen** (jede Adresse jedes Profils aus Sicht jedes Testkontos, dazu unveränderte Bio-, Nickname- und Farben-Formulare) — Zeile für Zeile identisch, kein einziger Fehlerstatus.
>
> **Backup-Wiederherstellung:** erneut geprobt (siehe `docs/DEPLOYMENT.md`), Zeilenzahlen, Constraints und Inhaltsprüfsumme identisch.
>
> **`DECISIONS.md`:** 74 Einträge (D-01 bis D-74), lückenlos, keiner „Offen"; D-56 als ersetzt durch D-74 markiert, D-73 um den Namen des Decorators präzisiert.

**Meilenstein v1.2 abgeschlossen** — das Profil ist bereit für Blogbeiträge und Kommentare.

---

# M4.1 · v1.2.1 — Feedback zum Test

Anlass: Rückmeldung zum Personality Test einsammeln, bevor Blogbeiträge und Kommentare kommen. Gestaltung und Begründung: D-75. Anforderungen: PRD §5.3 (FR-T18 bis FR-T20).

#### 4.11 · Feedback zum Test
**Abhängig von:** 2.10, 2.14 · **Anforderungen:** FR-T18, FR-T19, FR-T20, D-75, D-10, D-18
**Fertig, wenn:**
- [x] `quiz.Feedback` mit Bewertung (1–5, optional), Text (≤ 2000, optional) und Fragebogen-Version (optional); CheckConstraints in der Datenbank für Wertebereich und „mindestens eines von beiden"; kein Verweis auf `User`/`Profile`, keine IP-Adresse.
- [x] Ein Formular, zwei Orte: unter der Ergebnisseite (HTMX, Ergebnis bleibt stehen, Dank an Ort und Stelle) und unter `/feedback/` mit Link im Footer jeder Seite; ohne JavaScript normales POST mit Weiterleitung auf die Dankeseite.
- [x] Mit und ohne Login abgebbar; Gate gilt wie überall.
- [x] Rate Limit über eigenen Zähler (`core.FeedbackAttempt`, 5 je IP und Stunde); die Meldung ist auch bei HTMX sichtbar.
- [x] Django-Admin: Feedback nur lesbar, filterbar nach Version und Bewertung, durchsuchbar; `FeedbackAttempt` wie die anderen Zähler.
- [x] Datenschutzseite nennt Feedback (anonym, nicht löschbar, keine persönlichen Angaben) und die Protokollierung der IP-Adresse beim Absenden.
- [x] Test: Speichern mit Bewertung, Text oder beidem; leer, 0/6/Text als Bewertung, zu langer Text und unbekannte Version abgelehnt bzw. zu „keine Angabe"; HTMX-Bausteine ohne `<html>`; Rate Limit inklusive abgelaufener Einträge; Escaping beim erneuten Anzeigen; Datenbank-Constraints; Gate.

> Umsetzung: `apps/quiz/{models,forms,views}.py`, Bausteine `templates/quiz/_feedback_body.html` (Formular oder Dank, steht in der Live-Region `#feedback-body`) und `feedback.html`; `FeedbackForm` ist ein einfaches `Form`, kein `ModelForm`, damit die Fehlermeldung „Bewertung oder Text nötig" nicht zusammen mit der Constraint-Meldung doppelt erscheint. Im Browser geprüft (Ergebnisseite: leer absenden zeigt die Meldung ohne Seitenwechsel, Absenden zeigt den Dank und lässt das Ergebnis stehen, Version landet in der Datenbank; `/feedback/` bei 375 px ohne horizontales Scrollen, Bedienelemente 44 px hoch).

---

# M5 · v1.3 — Beiträge

Anlass: Nutzende sollen eigene Gedanken zu Farben und Kombinationen aufschreiben können, sichtbar im Profil und in den Color Infos. Gestaltung und Begründung: D-78, D-80, D-81. Anforderungen: PRD §5.7 (FR-B1 bis FR-B12). Erstmals sehen Nutzende Eingaben anderer (PRD R-7): Sicherheit (Markdown, Zugriff) kommt vor der Oberfläche. Jeder Task lässt die Anwendung lauffähig; die Reihenfolge ist bindend, wo Abhängigkeiten genannt sind.

#### 5.1 · App-Gerüst und Beitragsmodell
**Abhängig von:** — · **Anforderungen:** FR-B1, FR-B2, FR-B8, FR-B9, D-78
**Fertig, wenn:**
- [x] `apps/posts` angelegt und registriert, ARCHITECTURE §5 stimmt.
- [x] `Post` mit Autorin/Autor (`Profile`), Titel (≤ 120), Text (≤ 10 000), `colors` (kanonischer Code oder leer, `apps.colors.utils.canonical_code`), `visibility` (nur `public`), `created_at`, `edited_at`, `comment_seq`; Migration; Titel nicht leer als Constraint.
- [x] Ungültige Farbcodes (unbekannter Buchstabe, Doppelung, nicht kanonisch) werden abgelehnt.
- [x] `Post.objects.visible_to(profile)` ist die einzige Lesestelle; der Manager ist dokumentiert als der Weg, `Post.objects.all()` wird nirgends außerhalb von Tests benutzt.
- [x] Django-Admin (D-71: der Test verlangt alle Modelle registriert): Liste mit Autorin/Autor, Titel, Farben, Datum; Löschen möglich.
- [x] Test: Modell, Constraints, `visible_to` liefert öffentliche Beiträge; Löschen des Profils entfernt seine Beiträge.

> Umsetzung: `apps/posts/{models,admin}.py`, Migration `0001_post`. Die Farbregel steht dreifach: `RegexValidator` (Formulare, `full_clean`) und ein DB-Constraint mit demselben Muster `^W?U?B?R?G?$` (genau die kanonischen Codes, leer erlaubt) — ein `GW` fände im Grid nie seine Kombination. Auch die Textlänge (≤ 10 000, per `Length` im Constraint) und ein nichtleerer Titel sind in der Datenbank festgehalten. `Post.Visibility` kennt nur `public`, den Wert `friends` gibt es erst mit dem Feature; `visible_to(None)` liefert für Gäste nichts. Der Admin ist nur lesbar plus löschen (D-71, D-81). Zwei Indizes für die späteren Abfragen (Grid je Kombination, Profil-Tab). Die Rate-Limit-Grenzen (30 Beiträge, 60 Kommentare, 20 Meldungen je Stunde) kommen mit 5.3, 6.2 und 5.7.

#### 5.2 · Markdown-Rendering
**Abhängig von:** 5.1 · **Anforderungen:** FR-B3, D-80, R-7
**Fertig, wenn:**
- [x] `markdown-it-py` in `requirements/base.txt` (Bereichsangabe `>=4.0,<5` wie die übrigen Abhängigkeiten); die Abhängigkeit ist in ARCHITECTURE §3 vermerkt.
- [x] `apps/posts/markdown.py`: `render_markdown(text)` (Überschriften, fett/kursiv, Listen, Zitate, Code, Links; Roh-HTML, Bilder, Tabellen aus), `excerpt(text, limit=200)` (Klartext, an Wortgrenze gekürzt, mit „…"). Template-Filter für beides.
- [x] Links nur `http`/`https`, jeder mit `rel="nofollow noopener noreferrer"`.
- [x] **Injektionstest:** Skript-Tags, Ereignisattribute im Roh-HTML, `javascript:`-, `data:`- und `vbscript:`-Links, Bildsyntax, verschachtelte und unvollständige Konstrukte, HTML-Entities — nichts davon wird ausführbar oder zu Markup, weder in `render_markdown` noch im Auszug.
- [x] Test: leerer Text, sehr langer Text, Auszug kürzt an Wortgrenze, Überschriften und Listen erscheinen im Auszug als Text.

> Umsetzung: `apps/posts/markdown.py` (`render_markdown`, `excerpt`), Filter `markdown` und `excerpt` in `apps/posts/templatetags/posts_tags.py`. Preset `commonmark` mit `html: False`; Bilder zeigen nur ihren (escapten) Alternativtext, Links nur bei `http`/`https` (alles andere, auch `mailto:` und relative Adressen, bleibt als Text stehen), Überschriften eine Stufe tiefer (`#` → `<h2>`, höchstens `<h6>`, denn der Titel der Beitragsseite ist das `<h1>`), Codeblöcke bekommen die Klasse `language-…` nur bei einem echten Sprachnamen. Der Auszug entsteht aus den geparsten Tokens statt aus dem gerenderten HTML (Klartext, Entities aufgelöst, kein `safe`). Der Injektionstest (`test_markdown.py`, über 60 Eingaben) prüft die Ausgabe gegen eine **Positivliste** aus Tags, Attributen und Attributwerten statt nur gegen bekannte Zeichenketten; dazu ein Test, der die Positivliste selbst auf Fehlalarm prüft, und ein Robustheitstest mit pathologischen Eingaben (unter 2 Sekunden). Gegenprobe: Mit eingeschaltetem Roh-HTML schlagen 43, ohne Link-Prüfung 14 Tests fehl.

#### 5.3 · Beitrag schreiben, bearbeiten, löschen
**Abhängig von:** 5.1, 5.2, 4.6 · **Anforderungen:** FR-B1 bis FR-B4, FR-B11, D-78
**Fertig, wenn:**
- [x] `/posts/new/` (nur eingeloggt): Titel, Text, Farbwahl mit dem Fünfeck-Feld aus 4.6 (ohne Farbe = allgemein, ohne JavaScript Kontrollkästchen), `?colors=wg` belegt vor. Vorschau vom Server (Absende-Knopf `action=preview` am Editor selbst; mit HTMX kommt nur der Vorschau-Baustein, ohne JavaScript die Seite neu), derselbe Renderer wie die Anzeige.
- [x] `/posts/<id>/edit/` nur für die Autorin bzw. den Autor, alle anderen: 302 auf die Beitragsseite, ohne Änderung (auch bei POST). `edited_at` nur bei tatsächlicher Änderung (wie D-72).
- [x] `/posts/<id>/delete/`: GET zeigt die Bestätigung, POST löscht; nur die Autorin bzw. der Autor.
- [x] Grenze: 30 Beiträge je Person und Stunde aus den eigenen Zeilen, die Meldung ist auch bei HTMX sichtbar (wie bei D-75).
- [x] Test: Anlegen mit und ohne Farbe, Längengrenzen, fremde Person kann weder bearbeiten noch löschen, unveränderter Beitrag behält `edited_at`, Grenze greift.

> Umsetzung: `apps/posts/{forms,views,decorators,limits,urls}.py`, Templates `posts/post_form.html`, `_preview.html`, `post_confirm_delete.html`. `PostForm` (ein einfaches `Form`) normalisiert Zeilenenden (Browser schicken CRLF, gespeichert wird LF), prüft die Länge **nach** der Normalisierung und behält eingerückten Code am Textanfang; die Autorin bzw. der Autor steht nicht im Formular. `author_only` (`decorators.py`) ist das Gegenstück zu `owner_only` (D-73): Gäste zum Login, unbekannt oder unsichtbar 404, jede andere Person 302 auf die Beitragsseite. Die Vorschau berührt weder die Datenbank noch die Grenze und prüft nicht (auch ein halb fertiger Text lässt sich ansehen). Die Grenze (`POST_RATE_LIMIT_MAX_POSTS = 30` je Stunde) zählt aus den eigenen Zeilen (`limits.is_limited`, wiederverwendbar für Kommentare und Meldungen), betrifft nur das Anlegen, und die Meldung erscheint im Formular mit dem eigenen Text (Status 429). Ein Test ersetzt `visible_to` durch eine Prüfung, die nichts durchlässt: Beitragsseite, Bearbeiten und Löschen liefern dann 404.
>
> **Abweichungen vom Plan:** (1) Eine **vorläufige Beitragsseite** (`/posts/<id>/`: Titel, Nickname, Text, Bearbeiten/Löschen für die Autorin bzw. den Autor) ist schon hier dabei, damit Speichern und Bearbeiten ein Ziel haben; 5.4 baut sie aus. (2) Löschen leitet vorläufig auf das Profil, 5.5 stellt auf den Tab „Posts" um. (3) Das Farbfeld (`color_field_context`, Template `_color_field.html`) ist von `social` nach `colors` gezogen (`apps/colors/field.py`, `templates/colors/`), damit `posts` nicht von `social` abhängt (D-78); Verhalten und Tests der Profilfarben unverändert. (4) Bis 5.5/5.6 gibt es noch keinen Knopf zum Editor; er ist unter `/posts/new/` erreichbar. Im Browser geprüft: Fünfeck mit Vorbelegung `?colors=gw`, Klick auf eine Ecke, HTMX-Vorschau (Skript als Text, Bild als Alternativtext, `javascript:`-Link bleibt Text), Veröffentlichen, Bearbeiten mit vorbelegten Werten; bei 375 px kein horizontales Scrollen auch mit sehr langen Wörtern und Codezeilen, Bedienelemente 44 px hoch.

#### 5.4 · Beitragsseite
**Abhängig von:** 5.3, 4.8 · **Anforderungen:** FR-B5, FR-B8
**Fertig, wenn:**
- [x] `/posts/<id>/` (Login-Pflicht, Gate wie überall): Autorenkarte, Farbkombination als Link auf die Color Infos (oder „General"), Datum und „edited", gerenderter Text; für die Autorin bzw. den Autor „Edit" und „Delete".
- [x] Unbekannte ID und Beiträge, die `visible_to` ausschließt: 404.
- [x] Mobil ohne horizontales Scrollen; `<title>` nennt den Beitragstitel.
- [x] Test: Gast → Login, Zugriff, 404, Farb- und Allgemein-Anzeige.

> Umsetzung: `templates/posts/post_detail.html`, `apps/posts/combinations.py` (`combination_labels`: eine Abfrage für alle Codes einer Seite, damit Liste und Grid in 5.5/5.6 sie mitbenutzen; hat eine Kombination noch keinen Namen, stehen die Farbnamen da, „White · Green", FR-C11). Die Autorenkarte ist die Komponente aus 4.8 (`{% author_card post.author size="medium" %}`, mit Prefetch der Zuordnung); die Farbverknüpfung steht als Text („General" oder Kombinationsname), nicht nur als Farbe (NFR-6). Der Titel ist das einzige `<h1>`, Überschriften im Text beginnen bei `<h2>`. Datum als `<time>`, „edited" nur bei gesetztem `edited_at`. Im Browser bei 727 und 375 px geprüft: kein horizontales Scrollen, der Codeblock scrollt in sich, sehr lange Wörter brechen um, „Edit"/„Delete" 44 px hoch. Kommentare kommen mit v1.4 unter den Text.

#### 5.5 · Profil-Tab „Posts"
**Abhängig von:** 5.4, 4.3 · **Anforderungen:** FR-B6
**Fertig, wenn:**
- [x] Tab „Posts" in der Leiste (für alle Profile), Adresse `/u/<nickname>/posts/`; Reihenfolge Pinboard, Posts, Friends, Test history, Settings.
- [x] Liste untereinander, neueste zuerst, 10 je Seite mit Seitenlinks: Titel, Farbkombination, Datum, Auszug; die ganze Karte ist **ein** Link (kein Link in einem Link).
- [x] Eigene Person: „Write a post"; leerer Zustand mit Hinweis statt Fehler (fremd wie eigen).
- [x] Keine N+1-Abfragen (Kombinationsnamen einmal je Seite).
- [x] Test: Reihenfolge, Seitenwechsel, fremdes und eigenes Profil, leer.

> Umsetzung: `profile_posts` in `apps/social/views.py` (Adresse `/u/<nickname>/posts/`), Seitenlogik in `apps/posts/listing.py` (`author_posts_page`, `cards_for` — beides bereitet Task 5.6 mit vor), Templates `social/profile_posts.html`, `posts/_post_card.html` und `posts/_pagination.html` (allgemein, für die Kommentar-Liste in 6.4 wiederverwendbar). Die Karte ist ein einziger Link: der Titel, per `::after` über die ganze Karte gespannt (`.post-card__link`); die Kombination steht darin nur als Text. Der Auszug ist Klartext und per CSS auf vier Zeilen begrenzt. Eine Seite kostet drei Abfragen für die Beiträge (Zählung, Seite, Kombinationsnamen), unabhängig von der Zahl der Beiträge. Seitennummern unter 1 oder ungültig ergeben Seite 1 (Djangos `get_page` schickte `0` auf die letzte Seite), zu große die letzte. Löschen eines Beitrags leitet jetzt auf diesen Tab. Die Zugriffsmatrix der Social-App (`test_access_control.py`) kennt die neue Adresse. Im Browser geprüft: Klick auf den Auszug öffnet den Beitrag; bei 375 px kein horizontales Scrollen, ein Link je Karte, Seitenlinks 44 px hoch.

#### 5.6 · Color Infos: Grid mit Beiträgen
**Abhängig von:** 5.4, 1.8 · **Anforderungen:** FR-B7, FR-B8, D-78
**Fertig, wenn:**
- [x] Unterhalb der Eigenschaften (innerhalb `#colors-panel`, damit der HTMX-Austausch es mitnimmt): Beiträge mit **exakt** der gewählten Kombination, neueste zuerst, höchstens 6; ohne Auswahl kein Grid. Der Code ist kanonisch, die Reihenfolge der Auswahl spielt keine Rolle.
- [x] Karte: Titel, kleine Autorenkarte, Auszug (Klartext ≈ 200 Zeichen, zusätzlich per CSS auf wenige Zeilen begrenzt), Datum; die ganze Karte ist ein Link. CSS-Grid mit automatischer Spaltenzahl, mobil eine Spalte (NFR-3).
- [x] „Show all posts" führt auf `/colors/<code>/posts/` (Seiteneinteilung, 12 je Seite); „Write a post about this" öffnet den Editor mit vorbelegten Farben.
- [x] Leerer Zustand: kurzer Hinweis mit Link zum Schreiben. Gäste sehen nur „Log in to read and write posts", keinen Beitrag und keine Zahl.
- [x] Ansage der Änderung über die bestehende Live-Region unverändert, keine neuen Fokusfallen; jede Karte führt über **einen** Link (den Titel, über die ganze Karte gespannt) auf den Beitrag, dazu als einziges zweites Ziel der Nickname der Autorenkarte.
- [x] Test: exakter Treffer (Beitrag zu WG erscheint nicht bei W und nicht bei WGU), kanonischer Code, Höchstzahl, leerer Zustand, Gast, HTMX-Fragment enthält das Grid, Abfragen bleiben konstant.

> Umsetzung: `_posts_context` und `combination_posts` in `apps/colors/views.py` (`colors` liest aus `posts`, D-78), Auswahl in `apps/posts/listing.py` (`combination_grid`: höchstens 6, dazu ob es mehr gibt; `combination_posts_page`: 12 je Seite), Templates `colors/_posts_grid.html` (im `#colors-panel`, hinter den Eigenschaften), `colors/combination_posts.html` und die wiederverwendete Karte `posts/_post_card.html` mit den Schaltern `show_author` und `hide_combination`. Adresse der Liste: `/colors/<code>/posts/` (ungültiger Code 404, falsche Reihenfolge 301 wie bei den Color Infos). Ein Account ohne Profil bekommt das Grid nicht (statt eines Fehlers), Gäste nur den Hinweis mit Login-Link.
>
> **Abweichung vom Plan:** Eine Karte hat zwei Ziele statt einem — den Beitrag (Titel, über die ganze Karte gespannt) und den Nickname der Autorenkarte (Profil), der per `z-index` über der gespannten Fläche liegt. Ein Nickname als bloßer Text widerspräche der Autorenkarte (FR-P15); zwei Links, nebeneinander und nicht ineinander, sind das übliche Muster. **Gefunden und behoben:** Die Autorenkarte lud die fünf Farbwerte je Karte neu, sobald die Karte per `{% include %}` eingebunden ist (ihr Zwischenspeicher galt je Template, nicht je Anfrage); jetzt hängt er an der Anfrage (`social_tags._hex_by_code`), ein Test mit sechs Autoren hält die Abfragezahl konstant. Im Browser geprüft: Grid zweispaltig bei 727 px, einspaltig bei 375 px ohne horizontales Scrollen; HTMX-Wechsel der Auswahl tauscht das Grid mit aus (gleiches Dokument, Live-Region sagt „Bant" an); Liste mit „Show all posts".

#### 5.7 · Melden
**Abhängig von:** 5.4 · **Anforderungen:** FR-B10, FR-B11, D-81
**Fertig, wenn:**
- [x] `Report(reporter, post, reason, created_at, handled_at)`; einmal je Person und Beitrag (Unique-Constraint); Grund optional ≤ 500.
- [x] „Report" auf der Beitragsseite (nicht beim eigenen Beitrag): kleines Formular, HTMX-Bestätigung „Thank you, we will look at it", ohne JavaScript eine eigene Seite. Grenze 20 Meldungen je Person und Stunde.
- [x] Admin: Meldungen mit Link auf den Beitrag, Melder, Grund, Zeit; Filter offen/bearbeitet; Aktion „Als bearbeitet markieren". Löschen des Beitrags über das Admin entfernt die Meldung mit.
- [x] PRD §2.2 und D-81 stimmen mit dem Verhalten überein.
- [x] Test: doppelte Meldung, eigener Beitrag nicht meldbar, Grenze, Admin-Liste lädt, Meldung verschwindet mit dem Beitrag.

> Umsetzung: `Report` in `apps/posts/models.py` (Migration `0002_report`; `post` ist vorerst Pflicht, 6.5 macht es zusammen mit `comment` zur Alternative), `ReportForm`, `report_post` und `report_thanks` in `apps/posts/views.py` (`/posts/<id>/report/` und `…/report/thanks/`), Bausteine `posts/_report_body.html` und `report_form.html`, Bereich `#report` auf der Beitragsseite (Live-Region). Mit HTMX öffnet der Link „Report" das Formular an Ort und Stelle und ersetzt es nach dem Senden durch „Thank you, we will look at it."; ohne JavaScript sind es die eigene Seite und eine Dankeseite (Weiterleitung, wie beim Feedback, D-75). Der eigene Beitrag lässt sich nicht melden (302 auf die Beitragsseite, ohne etwas anzulegen); wer schon gemeldet hat, sieht statt des Formulars einen Hinweis, und zwei gleichzeitige Absendungen fängt der Unique-Constraint ab. Grenze `REPORT_RATE_LIMIT_MAX_REPORTS = 20` je Stunde aus den eigenen Zeilen, die Meldung ist auch bei HTMX sichtbar. Admin (`ReportAdmin`, nur lesbar plus löschen): Beitrag als Link auf die öffentliche Seite, Melder, Grund, Status, Filter „Open/Handled", Aktionen „als bearbeitet markieren" und „wieder öffnen". **Löschen** gibt es bewusst nur bei den Beiträgen („Posts"): Das Löschen eines Beitrags nimmt seine Meldungen mit, ein Test bestätigt es auch für den Weg über die Admin-Aktion. Datenschutzseite und Account-Löschung ziehen mit 5.8 nach. Im Browser geprüft: Link öffnet das Formular im selben Dokument, Absenden ersetzt es durch den Dank, die Meldung steht in der Datenbank.

#### 5.8 · Account-Löschung und Datenschutz
**Abhängig von:** 5.7, 2.14 · **Anforderungen:** FR-B12, D-78
**Fertig, wenn:**
- [x] Account-Löschung entfernt Beiträge und Meldungen der Person; Beiträge anderer bleiben unberührt.
- [x] Bestätigungsseite der Account-Löschung nennt Beiträge.
- [x] Datenschutzseite ergänzt: Beiträge (sichtbar für alle Angemeldeten, mit Autorenname), Meldungen (Melder nur für die Projektinhaberin sichtbar), Löschwege, Backups.
- [x] Test: Löschung mit Beiträgen und Meldungen; Datenschutzseite nennt beides.

> Umsetzung: Die Kaskade stand seit 5.1/5.7 (`Post.author` und `Report.reporter` verweisen mit `CASCADE` auf `Profile`, `Report.post` auf `Post`); neu ist der Nachweis über den echten Weg (`test_account_deletion.py`): Beiträge der Person, ihre gesendeten Meldungen **und** alle Meldungen zu ihren Beiträgen sind weg, Beiträge und Profile anderer bleiben, Grid, Tab und Beitragsseite zeigen nichts mehr von ihr. Ein Test hält fest, dass jeder Verweis der Posts-App auf ein Profil kaskadiert — kommt in v1.4 die Ausnahme dazu (Kommentare werden zu Hüllen, D-79), muss sie dort bewusst begründet werden. Bestätigungsseite: „… your posts, and the reports you sent" und „Your posts disappear for everyone, together with everything attached to them." Datenschutzseite: unter „What is stored" Beiträge (sichtbar für alle Angemeldeten, mit Nickname, im Profil und in den Color Infos) und Meldungen (nur für die Projektinhaberin sichtbar, nichts geschieht automatisch), unter „How long" und „How to delete" die Löschwege (eigene Beiträge bearbeiten/löschen, Löschen eines Beitrags nimmt seine Meldungen mit, Account-Löschung nimmt alles mit); die Aussagen zu Backups (14 Tage) gelten unverändert. Kommentare und Pins kommen mit 6.3 und 7.3 in dieselben Texte.

#### 5.9 · Release-Durchsicht v1.3
**Abhängig von:** 5.8 · **Anforderungen:** PRD §11 (v1.3)
**Fertig, wenn:**
- [x] Alle Abnahmekriterien aus PRD §11 (v1.3) durchgegangen und abgehakt.
- [x] Zugriffsschutz für jede neue Adresse geprüft (Gate, Login, Autorenrechte), auch für POST von Fremden.
- [x] Injektionstest zusätzlich im Browser: Beitrag mit Skript-Tag, `javascript:`-Link und Bildsyntax anlegen und in Beitragsseite, Profilliste, Grid, Vorschau und Admin ansehen.
- [x] Prüfung gegen `ARCHITECTURE.md`: einzige neue Abhängigkeit ist `markdown-it-py`, JavaScript-Umfang unverändert, kein `safe` auf Nutzereingaben außer `render_markdown`.
- [x] Backup-Wiederherstellung erneut geprobt, mit den neuen Tabellen.
- [x] `DECISIONS.md` vollständig; Hinweis für das Deployment: neue Migrationen, also `scripts/deploy_full.sh`.

> **Durchsicht (2026-09-20).** **Abnahme PRD §11 (v1.3):** (1) Schreiben, Bearbeiten, Löschen und Melden mit und ohne Farbe — `test_post_editor.py`, `test_reports.py`, im Browser durchgespielt. (2) Injektionstest — über 60 Eingaben gegen eine Positivliste in `test_markdown.py` (Beitrag, Auszug, Vorschau, Template-Filter) **und** im Browser (siehe unten). (3) Tab „Posts" und Grid mit exaktem Treffer und Auszug — `test_profile_posts_tab.py`, `test_colors_grid.py`. (4) Gäste sehen nirgends einen Beitrag, jeder Lesepfad geht durch `visible_to` — Zugriffsmatrix und Wächtertests (neu, s. u.). (5) Account-Löschung — `test_account_deletion.py`.
>
> **Zugriffsschutz:** Neu `test_access_control.py`: jede Adresse (`new`, `detail`, `edit`, `delete`, `report`, `report_thanks`, Kombinationsliste) ohne Gate → Gate, ohne Login → Login (GET und POST, nichts ändert sich), Fremde bei `edit`/`delete` → 302 auf die Beitragsseite ohne Änderung, die Autorin bzw. der Autor kann den eigenen Beitrag nicht melden; **CSRF** mit eingeschalteter Prüfung: jede schreibende Adresse antwortet ohne Token mit 403; ein Test meldet eine neue, nicht aufgenommene Adresse. Die Gegenprobe (CSRF-Schutz testweise ausgeschaltet) lässt den Test fehlschlagen.
>
> **Gefunden und behoben:** `views.py` zählte für die Beitragsgrenze über `profile.posts.all()` und damit an `visible_to` vorbei. Für die Grenze harmlos, aber es hätte die Regel aufgeweicht; jetzt `Post.objects.visible_to(profile).filter(author=profile)`.
>
> **Injektionstest im Browser:** Beitrag mit `<script>`, `<img onerror>`, `<iframe src=javascript:>`, `<svg onload>`, `javascript:`-Link, Bildsyntax auf einen fremden Server und einem Code-Fence mit `"><script>` im Info-String, dazu derselbe Text im Titel und als Meldungsgrund. Angesehen in Vorschau, Beitragsseite, Profilliste, Grid und im Admin (Beitragsliste, Beitrag, Meldungsliste, Meldung, Löschbestätigung): nirgends wurde etwas ausgeführt (`window.__pwned` blieb ungesetzt), es gibt keine Elemente, Ereignis-Attribute oder Verweise auf den fremden Server aus der Nutzlast — alles steht als escapter Text da; der einzige Link im Text ist der harmlose mit `rel="nofollow noopener noreferrer"`. Das einzige `<svg>` im Artikel ist das Profilbild der Autorenkarte.
>
> **Prüfung gegen `ARCHITECTURE.md`:** `test_architecture.py` liest den Quelltext: kein Lesezugriff auf `Post` an `visible_to` vorbei (nur `create`), kein `|safe`/`autoescape off`, `mark_safe` nur in `apps/posts/markdown.py`, Abhängigkeiten genau die bekannten plus `markdown-it-py`, `posts` importiert kein `social`. Gegenprobe für jeden der vier Wächter (Umgehung eingebaut, `|safe`, `bleach` in `requirements`, CSRF aus): jeder schlägt an. Diff seit v1.2: `requirements/base.txt` (eine Zeile), `.github/workflows/ci.yml` (D-76); `static/js`, `compose*.yaml`, `Dockerfile`, `Caddyfile` unverändert — das JavaScript-Budget (Test aus 4.9) hält.
>
> **Backup-Wiederherstellung:** siehe `docs/DEPLOYMENT.md`, „Ein viertes Mal geprobt" — Zeilenzahlen, Inhalts-Prüfsummen, Constraints und Indizes der neuen Tabellen identisch. **`DECISIONS.md`:** 82 Einträge (D-01 bis D-82), lückenlos, keiner „Offen". **Deployment:** neue Migrationen, also `scripts/deploy_full.sh` (siehe „Release-Hinweise v1.3").

**Meilenstein v1.3 abgeschlossen** — Beiträge sind schreib-, les-, melde- und löschbar; die Kommentare (v1.4) können darauf aufbauen.

---

# M6 · v1.4 — Kommentare

Anlass: Beiträge sollen diskutiert werden können. Gestaltung und Begründung: D-79. Anforderungen: PRD §5.7 (FR-B13 bis FR-B20).

#### 6.1 · Kommentarmodell und Nummernvergabe
**Abhängig von:** 5.9 · **Anforderungen:** FR-B14, FR-B15, D-79
**Fertig, wenn:**
- [x] `Comment` (Beitrag, Autorin/Autor `Profile` oder leer, `number`, Klartext ≤ 2000, `reply_to`, `created_at`, `deleted_at`); `unique (post, number)`; Migration.
- [x] Ein Dienst legt Kommentare an: Nummer in einer Transaktion mit `select_for_update` aus `Post.comment_seq`; `reply_to` muss zum selben Beitrag gehören und darf keine Hülle sein.
- [x] Nummern bleiben nach dem Löschen unbenutzt.
- [x] Test: Nummernfolge, **gleichzeitiges** Anlegen (zwei Transaktionen) ergibt verschiedene Nummern, fremder Beitrag als Bezug abgelehnt, Hülle als Bezug abgelehnt.

> Umsetzung: `Comment` in `apps/posts/models.py` (Migration `0003_comment`), Dienst `apps/posts/comments.py::create_comment()` — die einzige Stelle, die Kommentare anlegt. `author` verweist `on_delete=PROTECT` auf `Profile` statt `CASCADE` (anders als `Post.author`/`Report.reporter`, D-78): Ein Account lässt sich erst löschen, wenn seine Kommentare zuvor zur Hülle gemacht wurden (Task 6.3) — vergisst der Löschweg das, bricht `PROTECT` sauber ab, statt eine Zeile mit Autor, aber ohne Profil zu hinterlassen; zwei Tests belegen das (blockiert vs. funktioniert nach `author = None`). `reply_to` verweist `on_delete=SET_NULL` auf sich selbst: Ein (im Anwendungscode nie vorkommendes) hartes Löschen eines Kommentars lässt Antworten darauf stehen, nur die Referenz wird leer — bewusst kein `PROTECT`, das hätte das Kaskaden-Löschen eines ganzen Beitrags blockiert, sobald ein Kommentar Antworten hat. Der Dienst sperrt über `Post.objects.visible_to(author)` (FR-B9), nicht über `Post.objects` direkt — Task 5.9s Wächtertest verlangt das, ein eigener Test bestätigt außerdem, dass ein unsichtbarer Beitrag den Kommentar ablehnt. **Gleichzeitigkeit real geprüft:** zwölf echte Threads (`transaction=True`, eigene DB-Verbindung je Thread, gemeinsam losgelassen durch eine `Barrier`) bekommen zwölf verschiedene, lückenlose Nummern; Gegenprobe ohne `select_for_update()` lässt denselben Test in drei von drei Läufen mit doppelten Nummern scheitern.

#### 6.2 · Kommentare auf der Beitragsseite
**Abhängig von:** 6.1, 4.8 · **Anforderungen:** FR-B13, FR-B15, FR-B8
**Fertig, wenn:**
- [x] Liste flach, älteste zuerst; je Kommentar kleine Autorenkarte, `#n` (Anker `c-n`), Datum, Text (`linebreaks` + `urlize`, escaped), bei Antworten „↪ #m" als Sprung zum Bezug.
- [x] Formular unter der Liste (≤ 2000 Zeichen), Grenze 60 je Person und Stunde; mit HTMX erscheint der neue Kommentar ohne Seitenwechsel, sonst POST mit Weiterleitung auf den Anker.
- [x] „Reply" je Kommentar: `?reply=3#comment-form`, das Formular zeigt „Replying to #3" mit „Cancel"; ohne JavaScript nutzbar. Auf Hüllen kein „Reply".
- [x] Nur eingeloggt; Beiträge, die `visible_to` ausschließt, nehmen keine Kommentare an.
- [x] Test: Reihenfolge, Antwort-Verweis, Anker, Grenze, Gast, unsichtbarer Beitrag, Escaping (Injektionstest wie 5.2 gegen Kommentare).

> Umsetzung: `apps/posts/{forms,views}.py` (`CommentForm`, `add_comment`, `_comments_context`), Templates `posts/_comments_section.html` (Baustein `#comments`, Live-Region, HTMX-Ziel) und `posts/_comment.html`. `Comment.objects.for_post(post)` (Task 6.1) blendet Hüllen ohne Antworten schon jetzt aus — 6.3 muss dafür an den Templates nichts mehr ändern, nur den Löschweg selbst bauen. „Reply" ist ein reiner Navigationslink (`?reply=3#comment-form`, wie die Seitenlinks aus Task 5.5): kein eigenes JavaScript nötig, funktioniert dadurch aus sich heraus auch ohne JavaScript. Die Grenze (`COMMENT_RATE_LIMIT_MAX_COMMENTS = 60`) zählt wie bei Beiträgen und Meldungen aus den eigenen Zeilen; eine unbekannte oder veraltete `?reply=`-Nummer wird still zu „kein Bezug" (wie `?colors=`, Task 5.6), kein Formularfehler. Text als Klartext über Djangos `urlize`+`linebreaks` (D-80) — kein eigener Renderer nötig, an echten Angriffs-Nutzlasten sowie per Gegenprobe (Escaping kurz durch `|safe` ersetzt: 24 von 32 Fällen schlagen dann fehl) geprüft. Die Zugriffsmatrix aus Task 5.9 (`test_access_control.py`) kennt die neue Adresse `comment` (schreibend, nur POST). Im Browser geprüft: HTMX-Kommentar ohne Seitenwechsel, „Reply" mit Banner und Zurücksetzen nach dem Absenden, echte Formularübermittlung ohne JavaScript springt auf `#c-4` (`:target` greift), bei 375 px kein horizontales Scrollen, „Reply"/„Post comment" 44 px hoch.

#### 6.3 · Kommentar löschen, Hüllen, Account-Löschung
**Abhängig von:** 6.2 · **Anforderungen:** FR-B16, FR-B19, D-79
**Fertig, wenn:**
- [ ] Die Autorin bzw. der Autor löscht den eigenen Kommentar (Bestätigung); er wird zur Hülle (Text und Autor leer, `deleted_at`); Hüllen ohne Antworten werden nicht angezeigt, Hüllen mit Antworten als „#n deleted".
- [ ] Der Dienst „zur Hülle machen" ist derselbe für das Löschen, die Admin-Aktion und die Account-Löschung.
- [ ] Account-Löschung macht die Kommentare der Person unter fremden Beiträgen zu Hüllen, vor `user.delete()`; unter eigenen Beiträgen verschwinden sie mit dem Beitrag.
- [ ] Test: Hülle mit und ohne Antworten, fremde Person kann nicht löschen, Account-Löschung, Löschen eines Beitrags entfernt alle Kommentare.

#### 6.4 · Profil-Tab „Comments"
**Abhängig von:** 6.3, 4.3 · **Anforderungen:** FR-B17
**Fertig, wenn:**
- [ ] Tab „Comments" (für alle Profile), `/u/<nickname>/comments/`; Reihenfolge Pinboard, Posts, Comments, Friends, …
- [ ] Neueste zuerst, 10 je Seite: Auszug, `#n`, Titel des Beitrags als Link mit Sprung zum Kommentar, Datum. Hüllen und Kommentare unter unsichtbaren Beiträgen fehlen.
- [ ] Leerer Zustand; keine N+1-Abfragen.
- [ ] Test: Reihenfolge, Hüllen fehlen, Sprungziel stimmt.

#### 6.5 · Kommentare melden
**Abhängig von:** 6.2, 5.7 · **Anforderungen:** FR-B10, FR-B18, D-81
**Fertig, wenn:**
- [ ] `Report` bekommt `comment` als Alternative zu `post` (genau eines von beiden, Constraint; einmal je Person und Kommentar); Migration.
- [ ] „Report" je fremdem Kommentar; Grenze wie 5.7 gemeinsam für Beiträge und Kommentare.
- [ ] Admin: Meldung zeigt Beitrag oder Kommentar; Aktion „Kommentar zur Hülle machen" (D-81).
- [ ] Test: Constraint, Doppelmeldung, eigener Kommentar, Admin-Aktion.

#### 6.6 · Zähler neuer Kommentare und Antworten
**Abhängig von:** 6.4 · **Anforderungen:** FR-B20, D-79
**Fertig, wenn:**
- [ ] `PostSeen(profile, post, last_seen_number)`, angelegt bzw. angehoben, wenn die Autorin bzw. der Autor des Beitrags oder jemand mit eigenem Kommentar darunter die Beitragsseite öffnet oder selbst kommentiert.
- [ ] „Neu" = Kommentare **anderer** mit Nummer über dem Stand, unter eigenem Beitrag oder als Antwort auf einen eigenen Kommentar; nichts doppelt gezählt; Hüllen zählen nicht.
- [ ] Zahl am Tab „Posts" (nur eigenes Profil; Ziffer sichtbar, für Screenreader ausgeschrieben, nicht nur Farbe, NFR-6); Markierung „n new" je Beitrag im Tab „Posts" und je Kommentar im Tab „Comments".
- [ ] Höchstens eine zusätzliche Abfrage je Seite (keine Schleife über Beiträge).
- [ ] Test: Zählung, Zurücksetzen durch Öffnen, eigene Kommentare zählen nicht, fremde Antworten auf fremde Kommentare zählen nicht, Hüllen, Abfragezahl.

#### 6.7 · Release-Durchsicht v1.4
**Abhängig von:** 6.6 · **Anforderungen:** PRD §11 (v1.4)
**Fertig, wenn:**
- [ ] Alle Abnahmekriterien aus PRD §11 (v1.4) durchgegangen und abgehakt.
- [ ] Zugriffsschutz für alle neuen Adressen erneut geprüft; Kommentar-POSTs von Gästen und Fremden ändern nichts.
- [ ] Injektionstest im Browser gegen Kommentare (Beitragsseite, Tab „Comments", Admin).
- [ ] Nummernvergabe unter gleichzeitiger Last einmal von Hand nachgestellt (zwei Sitzungen kommentieren im selben Moment).
- [ ] Backup-Wiederherstellung erneut geprobt; `DECISIONS.md` vollständig; Deployment mit `scripts/deploy_full.sh`.

---

# M7 · v1.5 — Pinnwand

Anlass: Der Platzhalter „Coming soon" aus v1.2 wird ersetzt. Gestaltung und Begründung: D-82. Anforderungen: PRD §5.7 (FR-B21 bis FR-B24).

#### 7.1 · Pins
**Abhängig von:** 6.7 · **Anforderungen:** FR-B21, FR-B23, D-82
**Fertig, wenn:**
- [ ] `Pin(profile, post | comment, created_at)`: genau eines von beiden (Constraint), einmal je Person und Ziel; Kaskade beim Löschen des Beitrags bzw. des Profils; Migration.
- [ ] „Pin"/„Unpin" auf Beitragsseite und je Kommentar, für eigene und fremde Inhalte; HTMX schaltet um, ohne JavaScript ein POST mit Weiterleitung. Nur, was `visible_to` erlaubt; Hüllen lassen sich nicht pinnen.
- [ ] Test: Pinnen und Lösen, doppelt, Hülle, unsichtbarer Beitrag, Kaskade.

#### 7.2 · Pinnwand-Tab
**Abhängig von:** 7.1, 4.7 · **Anforderungen:** FR-B22
**Fertig, wenn:**
- [ ] Der Platzhalter „Coming soon" ist weg: Hauptbereich des Standardtabs zeigt die Pins der Person, zuletzt gepinnt zuerst, 10 je Seite; Sidebar unverändert.
- [ ] Eintrag: Art („Post"/„Comment"), Autorenkarte des **Originals**, Auszug, Datum, Link (bei Kommentaren mit Sprung zum Anker), bei der eigenen Person „Unpin". Die Ziel-Seite bleibt die einzige Volltext-Ansicht.
- [ ] Leerer Zustand mit Hinweis (eigen: wie man etwas pinnt; fremd: „Nothing pinned yet").
- [ ] Test: Reihenfolge, beide Arten, fremdes und eigenes Profil, leer; die alten Tests zum Platzhalter (Task 4.7) sind angepasst.

#### 7.3 · Sichtbarkeit und Aufräumen
**Abhängig von:** 7.2 · **Anforderungen:** FR-B23, D-78, D-82
**Fertig, wenn:**
- [ ] Die Anzeige filtert über `visible_to` der **ansehenden** Person; Hüllen und gelöschte Originale erscheinen nicht.
- [ ] Account-Löschung entfernt die Pins der Person und alle Pins auf ihre Beiträge; Kommentare, die zu Hüllen werden, verschwinden aus fremden Pinnwänden.
- [ ] Test: mit ersetzter (verschärfter) `visible_to` erscheint der Pin nicht; Hülle; Account-Löschung.

#### 7.4 · Release-Durchsicht v1.5
**Abhängig von:** 7.3 · **Anforderungen:** PRD §11 (v1.5)
**Fertig, wenn:**
- [ ] Alle Abnahmekriterien aus PRD §11 (v1.5) durchgegangen und abgehakt.
- [ ] **Bereitschaft für „nur Freunde":** ein Test ersetzt `visible_to` durch eine Prüfung, die nichts durchlässt, und ruft jeden Pfad auf, der Beiträge oder Kommentare zeigt (Beitragsseite, Kommentare, Tab „Posts", Tab „Comments", Grid, Liste je Kombination, Pinnwand, Zähler, Melden, Pinnen) — überall kein Inhalt bzw. 404. Ein neuer Lesepfad ohne `visible_to` fällt damit auf.
- [ ] Zugriffsschutz, Injektionstest, Backup-Wiederherstellung wie in 5.9/6.7 erneut; `DECISIONS.md` vollständig.

**Meilenstein v1.5 abgeschlossen** — Beiträge, Kommentare und Pinnwand stehen; „nur Freunde" ist eine Änderung an einer Stelle.

---

## Nicht in dieser Roadmap

Bewusst außerhalb, siehe PRD §8: Sichtbarkeit „nur Freunde" für Beiträge (Feld und zentrale Prüfung kommen mit v1.3, PRD §8.2), Bearbeiten von Kommentaren, Löschen fremder Kommentare unter dem eigenen Beitrag, Likes, Suche in Beiträgen, Entwürfe, Bilder in Beiträgen, fremd angelegte Profile, nutzerseitige Content-Bearbeitung der Color Infos, Kuratoren-Rechte, Auswertungen des sozialen Graphen, weitere Sprachen, Bild-Upload, Umzug in die Cloud.

Der **Cloud-Umzug** ist als eigener Lern-Task nach v1.0 vorgesehen und in `ARCHITECTURE.md` §12 vorbereitet.

---

## Kritischer Pfad

```
0.1 → 0.2 → 1.1 → 1.3 → 1.4 ─┐
                              ├→ 1.7 → 1.8 → 1.9 → 1.10 → 1.12   [v0.1]
      0.4 → 1.5 → 1.6 ────────┘
                                    ↓
                 2.1 → 2.2 → 2.4 ─┐
                                   ├→ 2.10 → 2.11 → 2.12          [v0.2]
                 2.6 → 2.7 → 2.8 → 2.9
                                    ↓
                 3.1 → 3.4 → 3.5                                  [v1.0]
                                    ↓
                 4.1 → 4.2 → 4.3 → 4.4                            [v1.2]
                  │     │     └→ 4.7 ─┐
                  │     └→ 4.8 ───────┴→ 4.9 → 4.10
                  └→ 4.5 → 4.6 ─────────────────↗
                                    ↓
      5.1 → 5.2 → 5.3 → 5.4 ─┬→ 5.5                             [v1.3]
                             ├→ 5.6
                             └→ 5.7 → 5.8 → 5.9
                                    ↓
      6.1 → 6.2 → 6.3 → 6.4 → 6.6 → 6.7                         [v1.4]
             └────→ 6.5 ────↗
                                    ↓
      7.1 → 7.2 → 7.3 → 7.4                                     [v1.5]
```

**Die drei Tasks mit dem größten Risiko in v0.1 bis v1.0:** 1.4 (Content-Erfassung, größter Einzelposten), 2.7 (Fragenqualität entscheidet über das Produktziel P2), 1.9 plus 1.10 (Fünfeck-Bedienung auf allen Geräten).

**Größtes Risiko in v1.3 bis v1.5:** 5.2 (Markdown darf nie zu ausführbarem HTML werden, PRD R-7), 6.1 (Kommentarnummern unter gleichzeitigem Schreiben) und 7.4 (jeder Lesepfad muss durch `visible_to` gehen, sonst ist „nur Freunde" später ein Datenleck).

**Größtes Risiko in v1.2:** 4.6 (Fünfeck als Formularfeld, zwei Wege der Farbwahl, Erhalt der Testverknüpfung) und 4.1 (URL-Umbau: alle Redirects und Links auf die neue Profil-URL, ohne Bestandsdaten anzufassen).
