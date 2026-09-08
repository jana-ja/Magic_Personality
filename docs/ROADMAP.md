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
- [x] **0 Farben:** Ziel und Mittel aller fünf Farben, am Fünfeck verortet.
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
- [ ] Klick tauscht nur das Info-Panel, `hx-push-url` aktualisiert die Adresse.
- [ ] Vor- und Zurück-Navigation stellt den richtigen Zustand her.
- [ ] Bei deaktiviertem JavaScript funktioniert weiterhin alles (nur als vollständiger Seitenaufruf).

#### 1.9 · Tastatur und Barrierefreiheit
**Ziel:** Bedienbar ohne Maus und mit Screenreader.
**Abhängig von:** 1.8 · **Anforderungen:** FR-C5, FR-C8, NFR-5, NFR-6
**Fertig, wenn:**
- [ ] `W U B R G` schalten die jeweilige Farbe um, `Esc` setzt zurück.
- [ ] Farben sind über Tab erreichbar, mit Enter und Leertaste bedienbar, sichtbar fokussiert.
- [ ] `aria-pressed` spiegelt den Zustand.
- [ ] Live-Region sagt nach dem Austausch den neuen Kombinationsnamen an.
- [ ] Hervorhebung schaltet sofort um, bevor die Antwort eintrifft.
- [ ] Eigenes JavaScript bleibt unter etwa 150 Zeilen und ohne Framework.

#### 1.10 · Mobiles Layout
**Ziel:** Eigenständige Gestaltung, keine skalierte Desktop-Ansicht.
**Abhängig von:** 1.9 · **Anforderungen:** NFR-3, D-14
**Fertig, wenn:**
- [ ] Fünfeck oben, alle Informationen als zusammenhängender Block darunter.
- [ ] Eigenschaften werden mobil **nicht** am Fünfeck verortet.
- [ ] Bei 375 px Breite ohne horizontales Scrollen bedienbar; Trefferflächen ausreichend groß.

#### 1.11 · Rechtliches und About
**Ziel:** Pflichtangaben und Quellenkennzeichnung.
**Abhängig von:** 0.4 · **Anforderungen:** PRD §9, D-12
**Fertig, wenn:**
- [ ] Footer: Quellenlink auf den Artikel. Der Fan-Content-Hinweis im vorgeschriebenen Wortlaut steht seit Task 1.5.
- [ ] About-Seite mit Kontaktangabe.
- [ ] Datenschutzseite als Platzhalter angelegt (Inhalt kommt mit 2.14, sobald personenbezogene Daten entstehen).

#### 1.12 · Erstes Deployment
**Ziel:** v0.1 läuft erreichbar auf dem kleinen Server.
**Abhängig von:** 1.10, 1.11, 0.6 · **Anforderungen:** NFR-10, D-29
**Fertig, wenn:**
- [ ] Caddy als Reverse Proxy mit automatischem TLS.
- [ ] Migrations laufen als **eigener Schritt**, nicht beim Containerstart.
- [ ] Deployment-Ablauf in `docs/DEPLOYMENT.md` dokumentiert und einmal von Grund auf durchgespielt.
- [ ] Zugangssperre greift auch in Produktion.
- [ ] `/healthz` von außen erreichbar, alles andere gesperrt.

**Meilenstein v0.1 abgeschlossen, wenn** alle Abnahmekriterien aus PRD §11 (v0.1) erfüllt sind.

---

# M2 · v0.2 — Test und Profil

#### 2.1 · Profil-Datenmodell
**Abhängig von:** 0.2, 1.1 · **Anforderungen:** FR-P1 bis FR-P5, D-07, D-22, D-27
**Fertig, wenn:**
- [ ] `Profile` mit `nickname`, `bio`, optionalem `user` (1:1).
- [ ] Eindeutigkeit des Nicknames über einen funktionalen Index auf `Lower("nickname")`.
- [ ] `ColorAssignment` mit `profile`, `author_profile`, Fremdschlüssel auf `ColorCombination`, `source`, optionaler Testreferenz.
- [ ] Test: zwei Profile mit `Alice` und `alice` sind nicht gleichzeitig anlegbar.

#### 2.2 · Registrierung, Login, Logout
**Abhängig von:** 2.1, 0.5 · **Anforderungen:** FR-U1 bis FR-U6, D-08
**Fertig, wenn:**
- [ ] Registrierung legt User und Profil gemeinsam an; Mindestlänge Passwort 10 Zeichen.
- [ ] Sessions in der Datenbank, Cookie `httpOnly`, `Secure`, `SameSite=Lax`.
- [ ] Passwortänderung beendet alle **anderen** Sessions.
- [ ] Rate Limiting auf Login und Registrierung (`django-axes`).
- [ ] Djangos Passwort-Reset-URLs sind **nicht** eingebunden (FR-U7).
- [ ] Test: nach Passwortänderung ist eine zweite Session ungültig.

#### 2.3 · Account löschen
**Abhängig von:** 2.2 · **Anforderungen:** FR-U8
**Fertig, wenn:**
- [ ] View mit ausdrücklicher Bestätigung.
- [ ] Profil, Farbzuordnung, Testhistorie und Freundschaftsbeziehungen werden mitgelöscht.
- [ ] Test: nach Löschung existiert keine Zeile mehr, die auf den Account verweist.

#### 2.4 · Profil ansehen und bearbeiten
**Abhängig von:** 2.2 · **Anforderungen:** FR-P1, FR-P4
**Fertig, wenn:**
- [ ] Nickname, Bio und Farben (1 bis 5, frei wählbar) bearbeitbar.
- [ ] Farbauswahl setzt `source = SELF_MANUAL` und leert die Testreferenz.
- [ ] Serverseitige Validierung; Nickname-Kollision wird verständlich gemeldet.

#### 2.5 · Generiertes Profilbild
**Abhängig von:** 2.4 · **Anforderungen:** FR-P3, D-13
**Fertig, wenn:**
- [ ] SVG wird deterministisch aus den hinterlegten Farben erzeugt, kein Upload, keine Dateiablage.
- [ ] Profil ohne hinterlegte Farben erhält eine neutrale Darstellung.

#### 2.6 · Fragebogen-Datenmodell
**Abhängig von:** 1.1 · **Anforderungen:** FR-T1 bis FR-T6, D-16
**Fertig, wenn:**
- [ ] `Questionnaire` mit Versionsnummer, `Question` mit `position` und `dimension`, `AnswerOption` mit Farbe.
- [ ] `TestResult` mit `profile`, Fragebogenversion, Zeitpunkt, `scores` als JSON, Ergebnisfarben.
- [ ] Seed-Command für Fragebögen; eine veröffentlichte Version ist unveränderlich.

#### 2.7 · Die 20 Fragen schreiben
**Abhängig von:** 2.6 · **Anforderungen:** FR-T2 bis FR-T4, R-3
**Fertig, wenn:**
- [ ] 20 Fragen mit je zwei Antworten in `seeds/questionnaire_v1.json`.
- [ ] Jedes der zehn Farbpaare kommt **genau zweimal** vor; jede Farbe erscheint in genau acht Fragen.
- [ ] Die vier Dimensionen (innen, außen, Gefühle, Werte) sind alle vertreten.
- [ ] Jede Frage schildert eine Situation; die Farbzuordnung wird nicht benannt.
- [ ] Automatischer Test prüft die Balance gegen die Seed-Datei.

> Qualitätsentscheidender Task (R-3). Eigene Sitzung, nicht nebenbei.

#### 2.8 · Test durchführen
**Abhängig von:** 2.7 · **Anforderungen:** FR-T7 bis FR-T9
**Fertig, wenn:**
- [ ] Freies Vor- und Zurückspringen vor der Abgabe, Antworten bleiben erhalten.
- [ ] Abgabe erst möglich, wenn alle 20 Fragen beantwortet sind; Fortschritt sichtbar.
- [ ] Kein serverseitiger Zwischenstand.
- [ ] Auch ohne Login durchführbar (Zugangssperre gilt trotzdem).

#### 2.9 · Auswertung
**Abhängig von:** 2.8 · **Anforderungen:** FR-T10 bis FR-T12, D-17
**Fertig, wenn:**
- [ ] Regel exakt wie FR-T11 umgesetzt, `T` über Einstellung konfigurierbar (Standard 2).
- [ ] Gleichstand an der Schnittgrenze nimmt alle betroffenen Farben auf.
- [ ] Ergebnis wird auf eine der 31 Kombinationen abgebildet.
- [ ] Tabellengetriebene Tests: klarer Dreier, deutlicher Zweier, deutlicher Vierer, Gleichstand an der Grenze, Gleichstand über alle fünf.

#### 2.10 · Ergebnis anzeigen und übernehmen
**Abhängig von:** 2.9, 2.4 · **Anforderungen:** FR-T13, FR-T14
**Fertig, wenn:**
- [ ] Ergebnis zeigt Kombinationsnamen, Punkte aller fünf Farben und verlinkt auf `/colors/<code>/`.
- [ ] Eingeloggt: Ergebnis landet automatisch in der Historie; Übernahme ins Profil wird **angeboten**, nicht erzwungen.
- [ ] Übernahme setzt `source = SELF_TEST` und die Testreferenz.

#### 2.11 · Ergebnis ohne Anmeldung
**Abhängig von:** 2.10 · **Anforderungen:** FR-T15, FR-T16, D-18
**Fertig, wenn:**
- [ ] Ergebnis wird im `localStorage` zwischengespeichert, Registrierung wird angeboten.
- [ ] Nach Registrierung **und** nach Login mit bestehendem Account wird es in die Historie übernommen und die Übernahme ins Profil angeboten.
- [ ] Zwischenspeicher wird danach geleert.
- [ ] Manipulierte oder veraltete Daten im Zwischenspeicher werden serverseitig abgewiesen, nicht übernommen.

#### 2.12 · Testhistorie
**Abhängig von:** 2.10 · **Anforderungen:** FR-P6 bis FR-P8, FR-T17, D-19
**Fertig, wenn:**
- [ ] Historie nur im eigenen Profil sichtbar, je Eintrag Datum, Punkte, Ergebnis.
- [ ] Einzelne Einträge löschbar.
- [ ] Löschen des referenzierten Eintrags leert die Referenz, lässt die Profilfarben aber bestehen.
- [ ] Test: fremde Historie ist über keinen Pfad erreichbar.

#### 2.13 · „Meine Farben auswählen"
**Abhängig von:** 2.4, 1.8 · **Anforderungen:** FR-C12
**Fertig, wenn:**
- [ ] Button erscheint nur bei angemeldeten Nutzenden mit hinterlegten Farben und führt auf den passenden Code.

#### 2.14 · Datenschutz und Backups
**Abhängig von:** 2.3, 1.12 · **Anforderungen:** PRD §9, NFR-9, ARCHITECTURE §11.4
**Fertig, wenn:**
- [ ] Datenschutzseite mit Inhalt: welche Daten, wo, wie lange, wie löschbar.
- [ ] Nächtlicher `pg_dump`, Aufbewahrung 14 Tage.
- [ ] **Eine Wiederherstellung wurde einmal erfolgreich durchgeführt** und dokumentiert.

**Meilenstein v0.2 abgeschlossen, wenn** alle Abnahmekriterien aus PRD §11 (v0.2) erfüllt sind.

---

# M3 · v1.0 — Social

#### 3.1 · Fremde Profile
**Abhängig von:** 2.4 · **Anforderungen:** FR-S1, D-19
**Fertig, wenn:**
- [ ] `/u/<nickname>/` zeigt Nickname, Bild, Bio, Farben — **nicht** Historie, **nicht** E-Mail.
- [ ] Nur für Angemeldete erreichbar.
- [ ] Test: Nicht-Angemeldete werden abgewiesen; Historie taucht in keiner Antwort auf.

#### 3.2 · Suche nach Nickname
**Abhängig von:** 3.1 · **Anforderungen:** FR-S2
**Fertig, wenn:**
- [ ] Teilstring-Suche, Groß- und Kleinschreibung egal, Treffer verlinken auf das Profil.

#### 3.3 · Suche nach Farbkombination
**Abhängig von:** 3.2 · **Anforderungen:** FR-S3, D-21, D-27
**Fertig, wenn:**
- [ ] Ergebnis sind alle Profile, deren Kombination die gesuchte **enthält**.
- [ ] Test: Suche „W" findet WU und WB; Suche „WU" findet WUB, aber nicht WB.
- [ ] Auswahl der Suchfarben nutzt dieselbe Darstellung wie das Fünfeck.

#### 3.4 · Freundschaften
**Abhängig von:** 3.1 · **Anforderungen:** FR-S4, D-20, D-22
**Fertig, wenn:**
- [ ] `Friendship` auf `Profile` (nicht auf `User`), Status PENDING oder ACCEPTED, mit Angabe wer angefragt hat.
- [ ] Constraint verhindert doppelte Paarungen in beiden Richtungen und Selbstfreundschaft.
- [ ] Anfrage senden, annehmen, ablehnen, bestehende Freundschaft auflösen.
- [ ] Offene Anfragen sind im eigenen Profil sichtbar.
- [ ] Test: Anfrage kann nicht doppelt gestellt und nicht von Dritten angenommen werden.

#### 3.5 · Freundeslisten und Graph
**Abhängig von:** 3.4 · **Anforderungen:** FR-S5, FR-S6
**Fertig, wenn:**
- [ ] Eigene Freundesliste im eigenen Profil.
- [ ] Freundesliste fremder Profile einsehbar und navigierbar.
- [ ] Über mindestens zwei Ebenen durchklickbar, ohne Sackgasse.

#### 3.6 · Release-Durchsicht v1.0
**Abhängig von:** 3.5 · **Anforderungen:** PRD §11 (v1.0)
**Fertig, wenn:**
- [ ] Alle Abnahmekriterien aus PRD §11 durchgegangen und abgehakt.
- [ ] Zugriffsschutz durchgeprüft: Gate, Login-Pflicht, private Historie.
- [ ] Prüfung gegen `ARCHITECTURE.md`: keine unbeabsichtigten Abweichungen.
- [ ] Backup-Wiederherstellung erneut geprobt.
- [ ] `DECISIONS.md` ist vollständig.

**Meilenstein v1.0 abgeschlossen** — das Produkt gilt als fertig.

---

## Nicht in dieser Roadmap

Bewusst außerhalb, siehe PRD §8: fremd angelegte Profile, nutzerseitige Content-Bearbeitung, Kuratoren-Rechte, Auswertungen des sozialen Graphen, weitere Sprachen, Bild-Upload, Umzug in die Cloud.

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
```

**Die drei Tasks mit dem größten Risiko:** 1.4 (Content-Erfassung, größter Einzelposten), 2.7 (Fragenqualität entscheidet über das Produktziel P2), 1.9 plus 1.10 (Fünfeck-Bedienung auf allen Geräten).
