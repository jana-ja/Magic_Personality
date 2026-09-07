# Entscheidungen — Magic Personality

Fortlaufendes Protokoll. Neue Einträge unten anhängen, alte nicht ändern — wird eine Entscheidung revidiert, bekommt sie den Status *Ersetzt durch D-xx* und der neue Eintrag verweist zurück.

**Status:** Angenommen · Offen · Ersetzt

---

### D-01 · Full Stack mit Datenbank ab v0.1
**Status:** Angenommen · 2026-09-05
Auch der zunächst statische Farb-Content liegt in der Datenbank, nicht in Dateien im Frontend.
**Warum:** Nutzende sollen diese Daten später bearbeiten und ergänzen. Ein späterer Umzug von statischen Dateien in eine Datenbank wäre ein Umbau, der jetzt vermeidbar ist.

### D-02 · Eine Entität für alle Farbkombinationen (n = 1..5)
**Status:** Angenommen · 2026-09-05
`ColorCombination` deckt Einzelfarben bis Fünffarb-Kombination ab. Alle 31 Zeilen werden vorab angelegt; fehlender Inhalt bleibt leer.
**Warum:** Die Überschneidungen überwiegen. Getrennte Entitäten je Größe hätten Abfragen und Templates verdreifacht, ohne echten Gewinn.

### D-03 · Eigenschaften speichern `leaning_toward` statt „left/right"
**Status:** Angenommen · 2026-09-05
`CombinationTrait.leaning_toward` verweist auf eine Farbe oder ist leer (center).
**Warum:** Links und rechts hängen davon ab, wie das Fünfeck gezeichnet ist. Eine Drehung oder ein abweichendes Mobil-Layout hätte die Daten falsch gemacht. Die Seite wird beim Rendern berechnet.

### D-04 · Ally/Enemy wird berechnet, nicht gespeichert
**Status:** Angenommen · 2026-09-05
Ergibt sich aus der Nachbarschaft im Farbrad.
**Warum:** Gespeicherte Redundanz kann widersprüchlich werden, berechnete nicht.

### D-05 · Perspektiven als eigene Entität, dreizeilig je Feindpaar
**Status:** Angenommen · 2026-09-05
`Perspective(combination, from_color | leer, text)`.
**Warum:** Dieselben Zeilen bedienen die Einzelfarb-Ansicht und die Paar-Ansicht. Der Inhalt existiert nur einmal.

### D-06 · Profilfarben sind frei wählbar, 1 bis 5 Farben
**Status:** Angenommen · 2026-09-05
Der Test bevorzugt drei Farben, erlaubt aber 1 bis 5. Das Profil ebenso.
**Warum:** Die Selbsteinschätzung soll Vorrang haben. Ein starres Dreier-Schema hätte dem Testergebnis widersprochen.

### D-07 · Herkunft der Profilfarben wird mitgespeichert
**Status:** Angenommen · 2026-09-05
`ColorAssignment.source` plus optionale Referenz auf das Testergebnis. Bei freier Wahl ist die Referenz leer.
**Warum:** Grundlage für eine spätere Kennzeichnung „durch Test bestätigt".

### D-08 · Serverseitige Sessions statt JWT
**Status:** Angenommen · 2026-09-05
Session-ID in einem `httpOnly`, `Secure`, `SameSite=Lax`-Cookie, Sessions in der Datenbank.
**Warum:** Sofort widerrufbar (Logout, Passwortänderung, Sperrung), nicht per JavaScript auslesbar, kein Refresh-Token-Aufbau. JWT löst verteilte Systeme — die es hier nicht gibt.

### D-09 · Zugangssperre für die gesamte Anwendung
**Status:** Angenommen · 2026-09-05
Geteilter Invite-Code vor allem anderen, dazu `noindex` und `robots.txt`.
**Warum:** Die Seite ist für 3–10 Personen gedacht. Nicht-öffentlich zu sein entschärft die rechtliche Lage erheblich und verhindert fremde Registrierungen.

### D-10 · Kein E-Mail-Versand in v1
**Status:** Angenommen · 2026-09-05
Keine Verifizierung, kein Self-Service-Passwort-Reset.
**Warum:** Vermeidet die einzige externe Infrastruktur im Projekt. Bei dieser Gruppengröße ist ein Reset manuell lösbar.
**Risiko:** R-1 im PRD. Sobald sich jemand aussperrt, wird Mailversand nachgerüstet.

### D-11 · Kein Tracking
**Status:** Angenommen · 2026-09-05
Keine Analytics, keine Third-Party-Skripte.
**Warum:** Inhaltlich unnötig — und erspart Cookie-Banner und Einwilligungsverwaltung vollständig.

### D-12 · Inhalte paraphrasieren, Quelle nennen, Symbole unter Fan Content Policy
**Status:** Angenommen · 2026-09-05
Keine wörtliche Übernahme aus dem Substack-Artikel; sichtbare Quellenangabe. Offizielle Mana-Symbole mit dem vorgeschriebenen Hinweis im Footer.
**Warum:** Nicht-kommerziell und nicht öffentlich; das hält die Nutzung im zulässigen Rahmen.

### D-13 · Profilbilder werden generiert, kein Upload
**Status:** Angenommen · 2026-09-05
Das Profilbild leitet sich aus den hinterlegten Farben ab.
**Warum:** Kein Objektspeicher, kein Moderationsbedarf, keine Missbrauchsfläche — und es passt inhaltlich besser als ein beliebiges Foto.

### D-14 · Desktop-first mit eigenständigem Mobil-Layout
**Status:** Angenommen · 2026-09-05
Mobil: Fünfeck oben, alle Informationen im Block darunter, Eigenschaften nicht am Fünfeck verortet.
**Warum:** Eine skalierte Desktop-Ansicht würde beim Fünfeck unlesbar. Zwei Layouts sind ehrlicher als ein schlechter Kompromiss.

### D-15 · i18n-Fähigkeit ab v0.1, ausgeliefert wird nur Englisch
**Status:** Angenommen · 2026-09-05
`locale`-Spalte auf allen Content-Modellen, UI-Texte über Übersetzungskataloge.
**Warum:** Nachträglich einzuziehen bedeutet, jede Zeile Anzeigetext noch einmal anzufassen. Jetzt kostet es fast nichts.

### D-16 · Fragebogen: 20 Fragen, je 2 Antworten, 1 Punkt, versioniert
**Status:** Angenommen · 2026-09-05
Jedes der 10 Farbpaare kommt genau zweimal vor; jede Farbe erscheint in 8 Fragen.
**Warum:** 20 Fragen mit zwei Antworten gehen als einzige Kombination perfekt balanciert auf. Die Versionsnummer hält alte Ergebnisse interpretierbar.

### D-17 · Auswertung über den größten Punktabstand mit Vorzug für drei Farben
**Status:** Angenommen · 2026-09-05
Standard drei Farben; zwei oder vier nur, wenn der jeweilige Abstand den Dreier-Abstand um mindestens `T` übersteigt (Standard `T` = 2). Gleichstand an der Grenze nimmt alle betroffenen Farben auf.
**Warum:** Macht „soll selten passieren" zu einer prüfbaren Regel mit genau einer Stellschraube.
**Offen:** `T` ist erst nach echten Durchläufen kalibrierbar (R-4).

### D-18 · Anonyme Testergebnisse im localStorage
**Status:** Angenommen · 2026-09-05
Übernahme sowohl nach Registrierung als auch nach Login mit bestehendem Account.
**Warum:** Kein serverseitiger Zustand für Nicht-Angemeldete, datenschutzrechtlich unproblematisch.

### D-19 · Testhistorie ist privat, Profile nur für Eingeloggte sichtbar
**Status:** Angenommen · 2026-09-05
**Warum:** Die Historie zeigt Entwicklung und Zweifel — das ist etwas anderes als die selbst gewählte Außendarstellung.

### D-20 · Freundschaft ist beidseitig und muss bestätigt werden
**Status:** Angenommen · 2026-09-05
In v1 ohne zusätzliche Rechte: Freundeslisten dienen dem Erkunden des Graphen.
**Warum:** Der spätere Wert liegt in der Auswertung des sozialen Graphen; dafür müssen Kanten bestätigt und damit belastbar sein.

### D-21 · Farbsuche findet Obermengen
**Status:** Angenommen · 2026-09-05
Suche „W" liefert auch WU und WB; Suche „WU" liefert auch WUB.
**Warum:** Entspricht der Frage, die tatsächlich gestellt wird („wer hat Weiß in sich?").

### D-22 · Profil ist von Account getrennt
**Status:** Angenommen · 2026-09-05
`Profile.user` ist optional; Freundschaften und Farbzuordnungen hängen an `Profile`, nicht an `User`. `ColorAssignment` kennt einen Autor.
**Warum:** Hält fremd angelegte Profile offen (§8.1 PRD), ohne in v1 Aufwand zu erzeugen. Nachträglich wäre es eine Migration quer durch das Datenmodell.

### D-23 · Architektur: Django-Monolith (Option C)
**Status:** Angenommen · 2026-09-06
Django 5.2 LTS, PostgreSQL, HTMX, Docker Compose, Caddy. Ausgewählt aus `ARCHITECTURE_OPTIONS.md`.
**Warum:** Kleinster Gesamtaufwand; Auth, Sessions, i18n, Migrations und ein Rechte-Grundgerüst kommen mit dem Framework.
**Bewusst in Kauf genommen:** geringerer DevOps-Lernwert als bei getrennten Artefakten. Wird über Reverse Proxy, getrennten Migrationsschritt, CI, Backups und einen definierten Cloud-Migrationspfad gezielt zurückgeholt.

### D-24 · Fünfeck über Progressive Enhancement statt JS-Insel
**Status:** Angenommen · 2026-09-06
Serverseitig gerenderte Links auf `/colors/<code>/`, per HTMX zu einem Teil-Austausch mit `pushUrl` beschleunigt. Rund 100 Zeilen eigenes JavaScript für Tastaturkürzel, sofortige Hervorhebung und Live-Region.
**Warum:** Vermeidet das im Vergleichsdokument benannte Hauptrisiko von Option C. Renderlogik existiert nur einmal, i18n und Barrierefreiheit funktionieren ohne Zusatzaufwand, der Zustand liegt ohnehin in der URL — und es funktioniert auch ohne JavaScript.

### D-25 · Kein Node.js im Projekt
**Status:** Angenommen · 2026-09-06
Kein Bundler, kein npm, kein Tailwind. CSS von Hand mit Custom Properties.
**Warum:** Folgt aus D-24. Container mit einer Laufzeit, Deployment mit einem Build-Schritt.

### D-26 · Eigenes User-Modell ab der ersten Migration
**Status:** Angenommen · 2026-09-06
`AbstractBaseUser` mit E-Mail als Anmeldefeld, ohne `username`.
**Warum:** Django lässt das User-Modell später nicht ohne Weiteres austauschen. Der Nickname gehört laut D-22 ohnehin an `Profile`.

### D-27 · Farbmengen als kanonischer Code, Profilfarben als Fremdschlüssel
**Status:** Angenommen · 2026-09-06
`ColorCombination.code` ist die in WUBRG-Reihenfolge sortierte Buchstabenfolge und zugleich die URL. `ColorAssignment` verweist per Fremdschlüssel darauf.
**Warum:** Die Farben einer Person *sind* eine der 31 Kombinationen. So gibt es nur eine Darstellung von Farbmengen im System, und die Obermengen-Suche aus D-21 wird zu einer einfachen Buchstabenprüfung.

### D-28 · Content als versionierte Seed-Dateien, Admin nur als Werkzeug
**Status:** Angenommen · 2026-09-06
`seeds/*.json` plus idempotentes Management-Command. Django Admin ist verfügbar, aber nicht die Quelle der Wahrheit.
**Warum:** Reproduzierbar, im Review sichtbar, in CI prüfbar. Reine Admin-Pflege würde beim nächsten Aufsetzen verloren gehen.

### D-29 · Migrations laufen als eigener Deploy-Schritt
**Status:** Angenommen · 2026-09-06
Nicht beim Containerstart.
**Warum:** Sonst migrieren mehrere Worker gleichzeitig, und ein Fehlschlag zeigt sich erst im Log statt im Deployment.

### D-30 · Lokales Docker Compose ohne Caddy, ohne TLS
**Status:** Angenommen · 2026-09-06
`compose.yaml` (Task 0.3) enthält nur `web` und `db`. `SECURE_SSL_REDIRECT` ist env-gesteuert mit Default `True`, lokal in `compose.yaml` explizit auf `False` gesetzt.
**Warum:** ARCHITECTURE.md §2 zeigt drei Container (inklusive Caddy) für den *produktiven* Aufbau; Task 0.3 verlangt für die *lokale* Entwicklung ausdrücklich nur `web` und `db`. Ohne einen TLS-terminierenden Proxy davor würde `SECURE_SSL_REDIRECT=True` in einer Endlosschleife enden (Weiterleitung auf `https://`, das lokal nie ankommt). Caddy und die produktionsscharfe Einstellung (`SECURE_SSL_REDIRECT=True`) kommen mit Task 1.12.

### D-31 · CI baut das Image bei jedem Push, veröffentlicht aber nur von `main`
**Status:** Angenommen · 2026-09-07
Der `build`-Job aus `.github/workflows/ci.yml` baut das Docker-Image auf jedem Push und jedem PR (fängt einen kaputten Dockerfile-Build sofort ab, unabhängig vom Branch), meldet sich bei der GitHub Container Registry aber nur an und veröffentlicht auch nur, wenn `github.ref == 'refs/heads/main'`.
**Warum:** ARCHITECTURE.md §11.3 nennt "Image-Build" als CI-Schritt, legt aber keine Branch-Policy fest. Ein Image bei jedem Feature-Branch-Push zu veröffentlichen würde die Registry mit nicht-deploybaren Zwischenständen zumüllen.
Zunächst lokal per `act` verifiziert (inkl. Postgres-Service-Container und einem absichtlich roten Lauf), dann live auf GitHub bestätigt (`github.com/jana-ja/Magic_Personality`) — der erste echte Lauf schlug beim Registry-Push mit `permission_denied: read_package` fehl. Ursache war ein verwaistes GHCR-Package `magic_personality` aus einem zuvor gelöschten, gleichnamigen Repository: gelöschte Repos nehmen ihre Packages nicht mit, und ein neues Repo gleichen Namens wird der alten Zugriffsliste nicht automatisch hinzugefügt. Nach Löschen des verwaisten Packages lief der Workflow durch.

### D-32 · `Perspective` erzwingt jetzt tatsächlich ein Enemy-Paar
**Status:** Angenommen · 2026-09-08
`Perspective.clean()` prüft seit Task 1.2 `combination.relation == Relation.ENEMY` statt nur "zwei Farben". Task 1.1 hatte das bewusst offengelassen (die Ally/Enemy-Berechnung existierte noch nicht) und dies im Code als TODO für Task 1.2 vermerkt.
**Warum:** PRD §6.1 spezifiziert `Perspective.combination` explizit als "2-Farb-**Enemy**-Kombination" — mit der jetzt vorhandenen Farbrad-Logik (Task 1.2) lässt sich das direkt und korrekt erzwingen, statt nur strukturell "irgendeine Zweierkombination" zuzulassen.

### D-33 · `Trait` bekommt (name, locale) als natürlichen Schlüssel, kein Slug-System
**Status:** Angenommen · 2026-09-08
`manage.py seed_content` (Task 1.3) erkennt eine Eigenschaft über `(name, locale)` wieder, nicht über eine externe ID/Slug. Ergänzend dazu jetzt ein echter DB-`UniqueConstraint` auf `Trait(name, locale)` (Migration `0003`), nicht nur eine Konvention im Import-Code.
**Warum:** Ein Slug-System (wie es die alte, ersetzte JSON-Datei mit IDs wie `"authority"` nutzte) wäre für den überschaubaren, kuratierten Bestand dieses Projekts über-engineered. Bewusste Kehrseite: den `name` einer Eigenschaft zu ändern legt eine neue Zeile an, statt die alte umzubenennen — dokumentiert in `seeds/README.md`.

### D-34 · `seeds/colors_en.json` startet leer, keine 31 Platzhalter-Einträge
**Status:** Angenommen · 2026-09-08
Die Produktions-Seed-Datei für Task 1.3 enthält `"combinations": []`. Alle Mechanik-Tests (Idempotenz, Validierung, Fehlerfälle) laufen gegen eigene, kleine Fixtures über `--path`, nie gegen diese Datei.
**Warum:** docs/ROADMAP.md trennt Task 1.3 (Mechanismus) bewusst von Task 1.4 (Content erfassen, "größter inhaltlicher Einzelposten... eigene Sitzung, nicht mit einem Coding-Task vermischen"). 31 Einträge mit leerem Inhalt vorab anzulegen hätte keinen Mehrwert gegenüber der bereits vorhandenen Datenmigration (Task 1.1) geboten und das Risiko erhöht, unfertigen Platzhaltertext versehentlich für echten Content zu halten.

### D-35 · Namen für 3er-, 4er- und Fünffarb-Kombinationen aus dem MTG-Sprachgebrauch
**Status:** Angenommen · 2026-09-07
Task 1.4 verlangt für diese 16 Kombinationen nur einen Namen. Die zehn Dreifarb-Namen (Esper, Grixis, Jund, Naya, Bant, Abzan, Jeskai, Sultai, Mardu, Temur) nennt die Quelle selbst. Die fünf Vierfarb-Namen (Artifice, Growth, Altruism, Aggression, Chaos) und der Fünffarb-Name (WUBRG) stehen dort nicht und stammen aus dem etablierten MTG-Sprachgebrauch.
**Warum:** Die Namen sind die einzige Verbindung zwischen unserer Ansicht und dem, was Spielende ohnehin sagen — sie zu erfinden würde die Ansicht für genau die Zielgruppe unbrauchbar machen, die den Farbkreis schon kennt. Es handelt sich um Bezeichner, nicht um übernommenen Fließtext; D-12 (paraphrasieren) bleibt für alle Inhaltstexte unberührt.

### D-36 · Eigenschaftsnamen sind projektweit eindeutig, statt zwischen Farben geteilt
**Status:** Angenommen · 2026-09-07
Keine zwei Kombinationen in `seeds/colors_en.json` verwenden denselben `traits[].name`. Wo sich Inhalte überschneiden, tragen sie unterschiedliche Namen — z. B. "Fairness" (White) neben "Procedural Fairness" (WU) oder "Protectiveness" (White) neben "Empathy" (Red).
**Warum:** `(name, locale)` ist der natürliche Schlüssel (D-33). Derselbe Name in zwei Kombinationen wäre **eine** `Trait`-Zeile mit **einer** Beschreibung und **einem** Typ — die zweite Nennung im Seed würde die erste stillschweigend überschreiben, statt eine zweite Eigenschaft anzulegen. Das ist als geteilte Eigenschaft grundsätzlich zulässig und gewollt, aber nur, wenn Beschreibung und Typ wirklich für beide passen. Solange es keinen inhaltlichen Grund für eine geteilte Zeile gibt, ist die eindeutige Benennung die risikoärmere Wahl; ein Test in `apps/colors/tests/test_seed_file_en.py` hält sie fest.
