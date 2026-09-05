# PRD — Magic Personality

**Status:** Entwurf v1 · **Datum:** 2026-09-05 · **Sprache Produkt:** Englisch (UI), i18n-fähig ab v0.1

---

## 1. Überblick

Magic Personality ist eine Full-Stack-Webanwendung rund um das Farbrad aus *Magic: The Gathering* (WUBRG) und die Persönlichkeitseigenschaften, die den fünf Farben und ihren 31 Kombinationen zugeschrieben werden.

Die Anwendung besteht aus drei Bereichen:

1. **Color Infos** — interaktives Fünfeck zum Erkunden von Farben, Farbkombinationen, deren Eigenschaften, Zielen, Archetypen und wechselseitigen Perspektiven.
2. **Personality Test** — ein Fragebogen, der die individuell stärksten Farben ermittelt.
3. **Social** — Profil mit eigener Farbkombination, Testhistorie, Suche und Freundesliste.

**Zielgruppe:** ein geschlossener Kreis von 3–10 Personen. Die Anwendung wird **nicht öffentlich beworben** und ist vollständig hinter einer Zugangssperre erreichbar.

**Charakter des Projekts:** privates, nicht-kommerzielles Spaß- und Lernprojekt. Neben dem Produkt selbst ist das Erkunden von DevOps- und Deployment-Themen ein ausdrückliches Ziel (siehe §9).

---

## 2. Ziele und Nicht-Ziele

### 2.1 Produktziele
- **P1** Die Farbphilosophie des MTG-Farbrads verständlich und explorativ vermitteln — insbesondere die *Perspektiven*, mit denen verfeindete Farben aufeinander blicken.
- **P2** Nutzenden eine glaubwürdige Selbsteinschätzung ermöglichen, die sich nicht wie ein austauschbares Internet-Quiz anfühlt.
- **P3** Den kleinen Nutzerkreis untereinander sichtbar machen: Wer ist welche Farbkombination?

### 2.2 Nicht-Ziele
- Kein öffentliches Produkt, kein Wachstum, keine Kommerzialisierung.
- Kein Deckbau, keine Kartendatenbank, kein Spielbezug über die Farbphilosophie hinaus.
- Kein Tracking, keine Analytics, keine Werbung.
- Keine Content-Moderation (kleiner, persönlich bekannter Nutzerkreis).
- Kein Social Login, kein Newsletter, keine Benachrichtigungen.

---

## 3. Nutzerrollen

| Rolle | Beschreibung |
|---|---|
| **Gast** | Hat den Invite-Code eingegeben, aber keinen Account. Kann Color Infos nutzen und den Test machen. Sieht keine Profile. |
| **Nutzer** | Registriert und eingeloggt. Zusätzlich: eigenes Profil, Testhistorie, Profile anderer, Suche, Freundesliste. |
| *(später)* **Kurator** | Darf Core-Content bearbeiten. Nicht in v1. |

---

## 4. Scope nach Meilensteinen

### v0.1 — Color Infos
Statischer Content aus der Datenbank, interaktives Fünfeck, keine Accounts. Invite-Gate aktiv.

### v0.2 — Test & Profil
Accounts, Personality Test, eigenes Profil mit Testhistorie. „Eigene Farben selektieren"-Button in den Color Infos.

### v1.0 — Social
Fremde Profile ansehen, Suche nach Nickname und Farbkombination, Freundesliste. Mit v1.0 gilt das Produkt als fertig.

---

## 5. Funktionale Anforderungen

### 5.1 Zugang (v0.1)

- **FR-A1** Die gesamte Anwendung liegt hinter einer Zugangssperre. Ohne gültigen Invite-Code ist keine Seite und kein API-Endpunkt außer der Code-Eingabe erreichbar.
- **FR-A2** Der Invite-Code ist ein geteiltes Geheimnis, serverseitig konfigurierbar, nicht im Code hinterlegt.
- **FR-A3** Nach erfolgreicher Eingabe bleibt der Zugang für dieses Gerät bestehen (langlebiges, `httpOnly` gesetztes Cookie).
- **FR-A4** Die Anwendung wird für Suchmaschinen gesperrt (`noindex`, `robots.txt`).

### 5.2 Color Infos (v0.1)

**Fünfeck (permanent sichtbar)**
- **FR-C1** Das Fünfeck steht mit einer Spitze nach oben. Von oben im Uhrzeigersinn: **White, Blue, Black, Red, Green**.
- **FR-C2** Jede Farbe wird als Symbol in einem Kreis plus Farbname dargestellt.
- **FR-C3** Das Fünfeck bleibt in **allen** Zuständen sichtbar; Selektionen verändern nur Hervorhebung und Info-Bereich.

**Selektion**
- **FR-C4** Jede Farbe ist einzeln an-/abwählbar (Toggle). Jede der 31 Teilmengen ist zulässig.
- **FR-C5** Es gibt eine Aktion „Auswahl zurücksetzen" (UI-Element und `Esc`).
- **FR-C6** Selektierte Farben werden hervorgehoben, nicht selektierte visuell zurückgenommen.
- **FR-C7** Die Selektion steht in der URL (z. B. `/colors/wu`), ist teilbar, per Deep-Link aufrufbar und über Vor-/Zurück-Navigation bedienbar. Kanonische Reihenfolge der Kürzel: WUBRG.
- **FR-C8** Tastaturkürzel `W`, `U`, `B`, `R`, `G` togglen die jeweilige Farbe.

**Angezeigte Informationen**

| Selektion | Anzeige |
|---|---|
| **0 Farben** | Ziel und Mittel jeder der fünf Farben, am Fünfeck verortet |
| **1 Farbe** | Name · Guiding Question · Eigenschaften (center bei der Farbe, tendierende Eigenschaften in Richtung des jeweiligen Nachbarn) · eigene Perspektive auf die beiden Feindfarben · Archetypen der vier Zweierkombinationen mit dieser Farbe |
| **2 Farben** | Beziehungstyp (Ally / Enemy) · Name · Guiding Question · Archetype · bei **Ally**: Eigenschaften · bei **Enemy**: alle drei Perspektiven (A über B, B über A, neutral) |
| **3–5 Farben** | Name (weitere Inhalte folgen, sobald sie erfasst sind — siehe FR-C11) |

- **FR-C9** Ally/Enemy wird aus der Nachbarschaft im Farbrad **berechnet**, nicht gespeichert.
- **FR-C10** Eigenschaften werden nach Typ (Strength / Weakness / Neutral) unterschieden. Die Unterscheidung wird **nicht allein farblich** kodiert (siehe NFR-6).
- **FR-C11** Fehlender Content (z. B. Eigenschaften einer 3er-Kombination) führt zu einem leeren, aber fehlerfreien Bereich — nicht zu einem Fehler oder einer leeren Seite.

**v0.2-Ergänzung**
- **FR-C12** Eingeloggte Nutzende mit hinterlegten Farben sehen einen Button „Meine Farben auswählen", der die Selektion entsprechend setzt.

### 5.3 Personality Test (v0.2)

**Aufbau**
- **FR-T1** Der Fragebogen besteht in Version 1 aus **20 Fragen mit je 2 Antwortmöglichkeiten**.
- **FR-T2** Jede Frage stellt eine Situation dar und bietet zwei typische Reaktionen zweier verschiedener Farben an. Die Zuordnung Antwort → Farbe ist für Testende nicht offensichtlich benannt.
- **FR-T3** Es gibt 10 ungeordnete Farbpaare; **jedes Paar kommt genau zweimal vor**. Damit erscheint jede Farbe in exakt 8 Fragen (max. 8 Punkte, 20 Punkte gesamt).
- **FR-T4** Die Fragen decken zusammen vier Dimensionen ab: innere Reaktionen, äußeres Verhalten, Gefühle sowie Werte und Ziele.
- **FR-T5** Jede gewählte Antwort gibt der zugehörigen Farbe **einen Punkt**.
- **FR-T6** Der Fragebogen trägt eine **Versionsnummer**. Fragen einer veröffentlichten Version werden nicht mehr verändert; Änderungen erzeugen eine neue Version.

**Ablauf**
- **FR-T7** Zwischen den Fragen kann frei vor- und zurückgesprungen werden, solange nicht abgegeben wurde.
- **FR-T8** Der Fortschritt wird nicht serverseitig gespeichert.
- **FR-T9** Alle Fragen müssen beantwortet sein, bevor abgegeben werden kann. Der Fortschritt ist sichtbar.

**Auswertung**
- **FR-T10** Die fünf Farben werden nach Punkten absteigend sortiert. `G(k)` bezeichnet den Punktabstand zwischen Rang `k` und `k+1`.
- **FR-T11** Ermittlung der Ergebnisgröße `k`:
  1. Standard ist `k = 3`.
  2. `k = 2` wird gewählt, wenn `G(2) ≥ G(3) + T`.
  3. `k = 4` wird gewählt, wenn `G(4) ≥ G(3) + T`.
  4. Treffen 2. und 3. zu, gewinnt der größere Abstand.
  5. `T` ist ein konfigurierbarer Schwellenwert, Standard **2 Punkte**. `T` ist so gewählt, dass Abweichungen von 3 Farben selten sind.
- **FR-T12** Punktgleichstand an der Schnittgrenze: Alle punktgleichen Farben werden aufgenommen. Das Ergebnis kann dadurch 1 bis 5 Farben umfassen.
- **FR-T13** Das Ergebnis nennt die resultierende Farbkombination mit ihrem Namen und verlinkt auf die zugehörige Ansicht in den Color Infos. Zusätzlich werden die Punktzahlen aller fünf Farben gezeigt.

**Nach dem Test**
- **FR-T14** *Eingeloggt:* Das Ergebnis wird automatisch in der Testhistorie gespeichert. Zusätzlich wird angeboten, es als Profilfarben zu übernehmen — verpflichtend ist das nicht.
- **FR-T15** *Nicht eingeloggt:* Das Ergebnis wird lokal im Browser (`localStorage`) zwischengespeichert und zur Registrierung eingeladen.
- **FR-T16** Meldet sich ein Gast anschließend an oder registriert sich, wird ein zwischengespeichertes Ergebnis wie unter FR-T14 behandelt (Historie + Angebot zur Übernahme) und der lokale Zwischenspeicher geleert.
- **FR-T17** Der Test kann beliebig oft wiederholt werden. Jeder Durchlauf erzeugt einen eigenen Historieneintrag.

### 5.4 Accounts (v0.2)

- **FR-U1** Registrierung mit E-Mail und Passwort. Voraussetzung ist ein gültiger Invite-Code (FR-A1).
- **FR-U2** E-Mail-Adressen sind eindeutig. Passwörter werden mit einem modernen Verfahren gehasht (Argon2id oder bcrypt).
- **FR-U3** Mindestlänge Passwort: 10 Zeichen. Keine Zeichenklassen-Zwänge.
- **FR-U4** Authentifizierung über **serverseitige Sessions** in einem `httpOnly`, `Secure`, `SameSite=Lax`-Cookie.
- **FR-U5** Logout beendet die Session serverseitig. Eine Passwortänderung beendet alle anderen Sessions.
- **FR-U6** Rate Limiting auf Login, Registrierung und Invite-Code-Eingabe.
- **FR-U7** **Kein** E-Mail-Versand in v1: keine Verifizierung, kein Self-Service-Passwort-Reset (siehe Risiko R-1).
- **FR-U8** Nutzende können ihren Account vollständig löschen. Dabei werden Profil, Testhistorie und Freundschaftsbeziehungen entfernt.

### 5.5 Profil (v0.2)

- **FR-P1** Jeder Account hat genau ein Profil mit: **Nickname**, **Bio** (Kurztext), **Profilbild**, **Farben**.
- **FR-P2** Der Nickname ist über **alle** Profile eindeutig (case-insensitiv verglichen).
- **FR-P3** Das Profilbild wird aus den hinterlegten Farben **generiert**. Kein Upload in v1.
- **FR-P4** Nutzende hinterlegen **1 bis 5 Farben** als eigenen Persönlichkeitstyp — frei wählbar oder aus einem Testergebnis übernommen.
- **FR-P5** Wird ein Testergebnis übernommen, wird die Referenz auf dieses Ergebnis gespeichert. Bei freier Wahl ist die Referenz leer. *(Grundlage für eine spätere Kennzeichnung „bestätigt".)*
- **FR-P6** Die **Testhistorie ist privat** und nur im eigenen Profil sichtbar. Jeder Eintrag zeigt Datum, Punkte pro Farbe und die resultierende Kombination.
- **FR-P7** Einzelne Historieneinträge können gelöscht werden.
- **FR-P8** Wird der Eintrag gelöscht, auf den die Profilfarben verweisen, bleiben die Farben bestehen; die Referenz wird geleert (FR-P5).

### 5.6 Social (v1.0)

- **FR-S1** Profile anderer sind **nur für eingeloggte Nutzende** sichtbar und zeigen: Nickname, Profilbild, Bio, Farben, Freundesliste. Nicht: Testhistorie, E-Mail.
- **FR-S2** Suche nach Nickname (Teilstring, case-insensitiv).
- **FR-S3** Suche nach Farbkombination: Ergebnis sind alle Profile, deren Farben die gesuchte Kombination **enthalten**. *(Suche „White" liefert auch WU und WB; Suche „WU" liefert auch WUB.)*
- **FR-S4** Freundschaften sind **beidseitig**: Anfrage senden, annehmen, ablehnen, bestehende Freundschaft auflösen. Offene Anfragen sind im eigenen Profil einsehbar.
- **FR-S5** Die eigene Freundesliste ist im eigenen Profil sichtbar.
- **FR-S6** Von einem Profil aus ist dessen Freundesliste einsehbar und deren Einträge sind navigierbar — der soziale Graph ist erkundbar.

---

## 6. Datenmodell

### 6.1 Content

**`Color`** — die fünf Farben als feste Stammdaten
`code` (W/U/B/R/G) · `name` · `symbol` · `hex` · `wheel_position` (0–4, im Uhrzeigersinn ab White)

**`ColorCombination`** — alle **31** Kombinationen, vollständig vorangelegt
`colors` (Menge, 1–5) · `name` · `goal` · `means` · `guiding_question` · `archetype` · `locale`

> Eine einzige Entität für n = 1..5, wie gewünscht. Felder ohne erfassten Inhalt bleiben leer — das ist bei 3er- und 4er-Kombinationen der Normalfall und kein Fehler.
> Nicht enthalten: `symbol` (gehört zur Farbe, Kombinationen rendern die Symbole ihrer Farben) und `ally/enemy` (wird aus der Nachbarschaft berechnet, FR-C9).

**`Trait`** — Eigenschaft
`name` · `description` · `type` (STRENGTH / WEAKNESS / NEUTRAL) · `locale`

> Der Typ beschreibt die allgemeine gesellschaftliche Sicht, nicht die Sicht einer bestimmten Farbe. Inhaltliche Überschneidungen sind ausdrücklich erlaubt (z. B. „Starrsinn" als Schwäche und „Beharrlichkeit" als Stärke).

**`CombinationTrait`** — Zuordnung Eigenschaft ↔ Kombination
`combination` · `trait` · `leaning_toward` (Color oder leer)

> Ersetzt `center / leaning left / leaning right`. Gespeichert wird **wohin** eine Eigenschaft tendiert, nicht auf welcher Bildschirmseite sie liegt — links/rechts ergibt sich beim Rendern aus der Position im Fünfeck und bleibt damit unabhängig von Layout und Orientierung.
> Bei Einzelfarben zeigt `leaning_toward` auf einen der beiden Nachbarn oder ist leer (center). Bei allen Mehrfarb-Kombinationen ist es immer leer.

**`Perspective`** — Sichtweisen innerhalb eines Feindpaares
`combination` (2-Farb-Enemy-Kombination) · `from_color` (Color oder leer = neutrale Sicht) · `text` · `locale`

> Drei Zeilen je Feindpaar. Dieselben Zeilen bedienen die Einzelfarb-Ansicht (`from_color` = selektierte Farbe, FR-C8) und die Paar-Ansicht (alle drei) — der Content existiert nur einmal.

### 6.2 Nutzerdaten

**`User`** — nur Zugangsdaten
`email` · `password_hash` · `created_at`

**`Profile`** — Darstellung einer Person
`nickname` (global eindeutig) · `bio` · `user` (**optional**, 1:1)

> **Bewusst getrennt von `User`.** In v1 hat jedes Profil genau einen User. Die Trennung hält den Weg zu fremd angelegten Profilen offen (§8.1), ohne in v1 Aufwand zu erzeugen.

**`ColorAssignment`** — die Farben einer Person
`profile` · `author_profile` · `colors` (1–5) · `source` (SELF_TEST / SELF_MANUAL) · `test_result` (optional) · `created_at`

> In v1 gilt immer `author_profile == profile`, und es existiert höchstens ein Datensatz je Profil. Als eigene Entität statt als Spalten am Profil, damit später mehrere Einschätzungen einer Person durch verschiedene Autoren möglich sind (§8.1).

**`Questionnaire`** — Fragebogen-Version
`version` · `question_count` · `published_at`

**`Question`** / **`AnswerOption`**
`questionnaire` · `position` · `text` · `dimension` (INNER / OUTER / FEELING / VALUES) · `locale`
je Option: `text` · `color` · `locale`

**`TestResult`** — Historieneintrag
`profile` · `questionnaire_version` · `taken_at` · `scores` (Punkte je Farbe) · `result_colors`

**`Friendship`**
`profile_a` · `profile_b` · `status` (PENDING / ACCEPTED) · `requested_by` · `created_at`

> Verweist auf `Profile`, nicht auf `User` — damit später auch fremd angelegte Profile Teil des Graphen sein können.

### 6.3 Mehrsprachigkeit
Content-Zeilen tragen eine `locale`-Spalte; fachlicher Schlüssel plus Locale sind zusammen eindeutig. In v1 existiert nur `en`. UI-Texte liegen in Sprachdateien, nicht in der Datenbank.

---

## 7. Nicht-funktionale Anforderungen

- **NFR-1 — Architektur:** Full-Stack-Anwendung mit Datenbank ab v0.1. Auch der zunächst statische Farb-Content liegt in der Datenbank, da er später durch Nutzende ergänzt werden soll.
- **NFR-2 — Desktop-first.** Das Desktop-Layout ist die primäre Gestaltung.
- **NFR-3 — Mobiles Layout ist eigenständig,** nicht nur skaliert: Fünfeck oben, alle Informationen in einem zusammenhängenden Block darunter. Eigenschaften werden mobil **nicht** am Fünfeck verortet.
- **NFR-4 — i18n-fähig ab v0.1:** keine fest im Code stehenden Anzeigetexte; Content lokalisierbar (§6.3). Ausgeliefert wird nur Englisch.
- **NFR-5 — Barrierefreiheit Fünfeck:** Farben sind echte Buttons mit `aria-pressed`, per Tab erreichbar, mit Enter/Space schaltbar. Änderungen der Selektion werden über eine Live-Region angesagt.
- **NFR-6 — Keine Information allein über Farbe.** Insbesondere Strength/Weakness/Neutral trägt zusätzlich Symbol oder Beschriftung.
- **NFR-7 — Kein Tracking, keine Analytics, keine Third-Party-Skripte.** Dadurch entfällt ein Cookie-Banner; gesetzt werden nur technisch notwendige Cookies.
- **NFR-8 — Sicherheit:** HTTPS, gehashte Passwörter, Rate Limiting auf Auth-Endpunkten, CSRF-Schutz bei zustandsändernden Anfragen, serverseitige Validierung aller Eingaben.
- **NFR-9 — Datenhaltung:** alles selbst gehostet oder bei einem Anbieter innerhalb der EU.
- **NFR-10 — Betrieb:** Start auf einem kleinen eigenen Server, späterer Umzug zu einem Cloud-Anbieter ist ausdrücklich vorgesehen. Deshalb: Konfiguration über Umgebungsvariablen, reproduzierbares Deployment, kein Anbieter-Lock-in.

---

## 8. Zukunftssicherheit

Diese Punkte sind **nicht** Teil von v1, beeinflussen aber Entscheidungen, die jetzt getroffen werden.

### 8.1 Fremd angelegte Profile
Nutzende sollen später Einschätzungen zu Personen anlegen können, die selbst keinen Account haben — damit der Freundeskreis auch dann als Graph analysierbar wird, wenn nicht alle mitmachen.

Vorbereitet ist:
- `Profile` ist von `User` getrennt → ein Fremdprofil ist ein Profil ohne User.
- Nicknames sind über alle Profile eindeutig → keine Kollision bei späterer Übernahme.
- `Friendship` verweist auf `Profile` → Fremdprofile sind graphfähig.
- `ColorAssignment` kennt einen `author_profile` → mehrere Einschätzungen derselben Person durch verschiedene Autoren sind ohne Umbau möglich.

Noch zu entscheiden, wenn das Feature kommt: Kennzeichnung als fremd erstellt · nur Name und Farbeinschätzung, keine persönlichen Inhalte · Übernahme oder Löschung durch die betroffene Person · Umgang mit Duplikaten · Darstellung abweichender Einschätzungen.

### 8.2 Weitere Ideen
- Nutzende ergänzen fehlende Inhalte zu 3er-, 4er- und 5er-Kombinationen.
- Rechtekonzept: kuratierte „Facts" gegenüber unbestätigten Nutzereindrücken.
- Auswertungen des sozialen Graphen (Farbverteilung im direkten und im erweiterten Umkreis).
- Farbinfos um typisches Verhalten und Erkennungsmerkmale erweitern.
- Weitere Sprachen.
- Profilbild-Upload (dann mit Moderationskonzept).

---

## 9. Rahmenbedingungen

- **Content-Herkunft:** Grundlage ist <https://homosabiens.substack.com/p/the-mtg-color-wheel>. Inhalte werden **paraphrasiert**, nicht wörtlich übernommen; der Artikel wird sichtbar als Quelle genannt. Das Erfassen der Daten in das hier definierte Modell ist eine eigene Aufgabe innerhalb von v0.1 und ersetzt die bestehende KI-generierte JSON-Datei.
- **Markenrechte:** Die offiziellen Mana-Symbole werden unter der *Wizards of the Coast Fan Content Policy* verwendet. Der geforderte Hinweis steht im Footer: Unofficial Fan Content, nicht von Wizards genehmigt oder unterstützt; verwendete Materialien sind Eigentum von Wizards of the Coast. Voraussetzung ist die durchgehende Nicht-Kommerzialität.
- **Rechtstexte:** Kontaktangabe auf einer About-Seite. Kurze Datenschutzseite (welche Daten, wo, wie lange, wie löschbar) plus funktionierende Account-Löschung (FR-U8). Kein Cookie-Banner nötig (NFR-7).
- **Lernziele:** DevOps und Deployment werden bewusst mit erkundet (NFR-10). Die Wahl des Technologie-Stacks erfolgt in einem eigenen Schritt (`docs/ARCHITECTURE.md`); dieses PRD bleibt stack-neutral.

---

## 10. Offene Punkte und Risiken

| ID | Punkt | Umgang |
|---|---|---|
| **R-1** | Kein Passwort-Reset (FR-U7). Wer sein Passwort vergisst, kommt nicht mehr hinein. | Bei 3–10 Personen manuell lösbar. Sobald es einmal auftritt: E-Mail-Versand nachrüsten. |
| **R-2** | 3er- bis 5er-Kombinationen zeigen in v1 nur den Namen. | Bewusst akzeptiert; Inhalte kommen später durch Nutzende. |
| **R-3** | Qualität der 20 Testfragen entscheidet über P2. | Fragen werden als eigener, abgegrenzter Task erstellt und gegen FR-T2 bis FR-T4 geprüft. |
| **R-4** | Schwellenwert `T` (FR-T11) ist erst nach echten Durchläufen kalibrierbar. | Konfigurierbar halten, Standard 2. |
| **R-5** | Das Fünfeck ist die anspruchsvollste UI-Aufgabe, besonders mobil. | Zwei eigenständige Layouts (NFR-3), früh im Meilenstein einplanen. |
| **R-6** | Fremdprofile berühren personenbezogene Daten Dritter. | Nicht in v1. Anforderungen dazu in §8.1 festgehalten. |

---

## 11. Abnahmekriterien je Meilenstein

**v0.1**
- Invite-Gate schützt die gesamte Anwendung.
- Alle 31 Kombinationen liegen in der Datenbank; Farb-, Eigenschafts- und Perspektiven-Content ist für alle Einzelfarben und alle 10 Zweierkombinationen erfasst.
- Jede der 31 Selektionen zeigt korrekte Inhalte, ohne Fehler bei fehlendem Content.
- Selektion funktioniert per Maus, Tastatur und Deep-Link; die URL spiegelt den Zustand.
- Desktop- und Mobil-Layout sind je eigenständig umgesetzt.

**v0.2**
- Registrierung, Login, Logout, Account-Löschung funktionieren; Sessions sind widerrufbar.
- Fragebogen v1 mit 20 Fragen erfüllt die Paar-Balance aus FR-T3 nachweislich (per Test abgesichert).
- Auswertung folgt FR-T10 bis FR-T12; die Regel ist mit Beispielfällen getestet.
- Ergebnisübernahme funktioniert eingeloggt wie auch über den Zwischenspeicher nach Registrierung oder Login.
- Profil zeigt Farben und private Historie; Löschen eines Eintrags verhält sich nach FR-P8.

**v1.0**
- Fremde Profile sind nur eingeloggt sichtbar und zeigen keine Historie.
- Beide Suchen liefern korrekte Ergebnisse, insbesondere die Teilmengen-Logik aus FR-S3.
- Freundschaftsanfragen lassen sich senden, annehmen, ablehnen und auflösen.
- Über Freundeslisten ist der Graph navigierbar.
