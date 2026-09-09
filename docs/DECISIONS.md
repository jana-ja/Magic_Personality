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

### D-37 · Fünfeck-Beschriftung: `theme` an der Kombination, `PerspectivePole` je Konfliktende
**Status:** Angenommen · 2026-09-08
Die kurzen Wörter, die im Fünfeck an Kanten und Diagonalen stehen, sind zwei neue Strukturen: `ColorCombination.theme` (ein Wort je Zweierkombination — bei Ally das gemeinsame Anliegen „Design", bei Enemy das Ergebnis der Kombination „Tribalism") und `PerspectivePole(perspective, color, term)` — je Perspektive genau zwei Zeilen, eine an jedem Ende der Feind-Diagonale. Zusätzlich sind `goal` und `means` der Einzelfarben auf je ein Wort gekürzt („peace" / „order"), weil sie an der Fünfeck-Ecke stehen. Referenz sind die fünf Zeichnungen in `docs/reference/`.
**Warum:** Ein früherer Entwurf hatte ein Feld `summary` („Complacency vs. optimization") plus ein Feld `pole` je Farbe. Beides passte nicht: Die beiden Hälften einer Dichotomie stehen an gegenüberliegenden Enden einer Linie, müssen also einzeln adressierbar sein; und die Zerlegung passiert bei **jedem** Blickwinkel, nicht nur beim neutralen — die neutrale Sicht auf W/B trägt „Group" und „Individual". Ein eigenes Modell statt zweier Spalten `term_a`/`term_b` an `Perspective`, weil die Zuordnung Wort → Farbe hier der ganze Inhalt ist: über die Position in einer Spalte wäre sie nur implizit, und ein vertauschtes Paar („Good" bei Schwarz) wäre eine Bedeutungsumkehr, die keine Validierung finden könnte. Ally-Paare brauchten ohnehin ein eigenes Feld — `Perspective` ist seit D-32 enemy-only, und `archetype` („The Architect") ist etwas anderes.

### D-38 · URL-Form der Selektion: kleingeschrieben, WUBRG-sortiert
**Status:** Angenommen · 2026-09-08
`/colors/<code>/` verwendet kleingeschriebene Buchstaben in WUBRG-Reihenfolge (`"wu"`, nicht `"WU"` oder `"uw"`) — anders als `ColorCombination.code`, das großgeschrieben ist. Groß-/Kleinschreibung *und* Reihenfolge zählen gemeinsam als "kanonisch"; jede Abweichung in beidem löst denselben permanenten Redirect aus. Die reine Auswahl-Logik (Parsen, Kanonisieren, Toggle) liegt in `apps/colors/selection.py`, getrennt von der Geometrie in `pentagon.py`.
**Warum:** PRD §5.2 (FR-C7) und Roadmap 1.6 nennen in ihren Beispielen durchgehend Kleinschreibung (`/colors/wu`, Redirect-Beispiel `/colors/uw/`) — ARCHITECTURE.md §6.2 legt die Groß-/Kleinschreibung der URL nicht separat fest, nur dass `code` "direkt die URL" liefert. Kleingeschriebene URLs sind zudem die übliche Web-Konvention.

### D-39 · `{% localize off %}` um jede SVG-Geometrie im Template
**Status:** Angenommen · 2026-09-08
`templates/colors/_pentagon.html` umschließt den gesamten `<svg>`-Block mit `{% localize off %}` … `{% endlocalize %}`.
**Warum:** Bei Task 1.6 zeigte sich beim Testen mit einem auf Deutsch eingestellten Browser: Django formatiert rohe `float`-Werte im Template nach der aktiven Sprache — `23.336` wird zu `23,336`. Für Anzeigetext ist das erwünscht, für SVG-Koordinaten macht es das Attribut ungültig, ohne dass ein Fehler auftritt; die Figur zeichnet sich einfach falsch (Ecken kollabieren sichtbar auf einen Punkt). Betroffen sind nur roh übergebene `float`-Werte — `outline_points`, `star_points` und `view_box` sind in `pentagon.py` bereits zu Strings vorformatiert (`f"{x:.3f}"`) und daher immun, das war der Unterschied, an dem sich der Fehler eingrenzen ließ. `{% localize off %}` um den ganzen Block statt einzelner `|unlocalize`-Filter je Zahl, damit Task 1.7s weitere Koordinaten (Pol-Beschriftungen an den Diagonalen) automatisch denselben Schutz bekommen, statt dass er an jeder neuen Stelle erneut mitgedacht werden muss. Ein Regressionstest rendert die Seite mit aktivem Deutsch und prüft auf Komma-Dezimaltrenner in numerischen Attributen.

### D-40 · 1-Farbe-Box zeigt Allies/Enemies statt Archetypen-Ausblick und Perspektiven-Text
**Status:** Angenommen · 2026-09-08
Die Info-Box bei einer selektierten Farbe zeigt eine Liste ihrer beiden Ally- und beiden Enemy-Farben (Namen, sonst nichts). Das ersetzt zwei ursprünglich in PRD §5.2 vorgesehene Inhalte für diesen Zustand: die vollständigen Archetypen-Namen der vier Zweierkombinationen mit dieser Farbe, und die eigene Perspektive (Fließtext) auf beide Feindfarben.
**Warum:** In der Design-Runde zu Task 1.7 (mehrere Entwürfe, siehe die Artifact-Historie) hat sich gezeigt, dass beide Inhalte einen Klick entfernt ohnehin vollständig verfügbar sind — Guiding Question und Archetype einer Zweierkombination erscheinen beim Auswählen des jeweiligen Paares selbst, die Perspektiven-Texte beim Auswählen des jeweiligen Feindpaares. Die Allies/Enemies-Liste macht stattdessen sofort sichtbar, *wohin* ein weiterer Klick führen würde, ohne die Info-Box bei einer einzelnen Farbe mit vier Archetyp-Namen und zwei Textabsätzen zu überladen. PRD §5.2 ist entsprechend angepasst.

### D-41 · Info-Box ist immer sichtbar, auch ohne Selektion
**Status:** Angenommen · 2026-09-08
Die Info-Box neben (Desktop) bzw. unter (Mobil) dem Fünfeck wird jetzt auch bei 0 Farben gerendert — mit einem Platzhaltertext und einem `Reset selection`-Link, der schlicht auf sich selbst zeigt. Ersetzt eine Task-1.6-Festlegung, nach der weder Box noch Reset-Link ohne Selektion erschienen.
**Warum:** In der Design-Runde zu Task 1.7 hat sich die reservierte Fläche als die bessere Lösung erwiesen: Ohne sie verschiebt die erste getroffene Farbwahl das gesamte Seitenlayout (die Box erscheint neu und drängt den nachfolgenden Inhalt), mit ihr bleibt die Seitenstruktur über alle Selektionsgrößen hinweg stabil. Der zugehörige Task-1.6-Test (`test_no_reset_link_when_nothing_is_selected`) ist durch eine Prüfung der neuen Erwartung ersetzt.

### D-42 · Halo-Farbe getrennt von der Identitätsfarbe, mit einer Ausnahme für Weiß
**Status:** Angenommen · 2026-09-08
`pentagon.py` bekommt eine eigene `HALO_OVERRIDES`-Konstante (`{"W": "#F4C430"}`) plus `halo_color()`. Der Selektions-Halo (Task 1.6, FR-C6) nutzt für vier Farben weiterhin direkt `Color.hex`, für Weiß einen kräftigeren, gelb gehaltenen Wert.
**Warum:** Weiß' offizieller Mana-Hex-Wert (`#F8F6D8`) ist ein blasses Creme, das als weicher Halo auf dem Seitenhintergrund praktisch nicht zu erkennen ist — in der Design-Runde ausdrücklich bemängelt. `Color.hex` bleibt unverändert die echte, offizielle Identitätsfarbe (für spätere Verwendungszwecke wie FR-P3 relevant); der Kompromiss sitzt bewusst nur in der Präsentationsschicht (`pentagon.py`), nicht in den Stammdaten.

### D-43 · Enemy-Diagonale trägt bei Selektion zusätzlich ihr eigenes Thema
**Status:** Angenommen · 2026-09-08
Bei zwei selektierten Enemy-Farben zeigt deren Diagonale zusätzlich zu den neutralen Pol-Wörtern das Thema der Kombination (`ColorCombination.theme`, z. B. "Tribalism" für WB) als Pill auf der Linienmitte — genau wie ein Ally-Paar sein gemeinsames Anliegen zeigt.
**Warum:** PRD §5.2 hatte das für den Enemy-Fall bereits so festgelegt ("nur X–Y, neutrale Sicht, **plus das Wort des Paares auf der Linie**"), die frühen Entwürfe der Design-Runde hatten es aber schlicht vergessen umzusetzen — beim Bauen der echten Ansicht aufgefallen und nachgezogen, keine neue Festlegung.

### D-44 · Fünfeck-Radius vergrößert, um Kollisionen der neuen Linienbeschriftungen zu vermeiden
**Status:** Angenommen · 2026-09-08
`pentagon.VERTEX_RADIUS` steigt von 34 auf 44; `THEME_LABEL_OUTWARD` und `POLE_LABEL_INSET` sind ebenfalls angepasst (mehr Abstand zwischen Kanten-Pill und Diagonalen-Pol nahe der Mitte).
**Warum:** Beim Testen im echten Browser (nicht nur per pytest) überlappten sich bei 0 Farben zwei Beschriftungen desselben Bereichs — das Enemy-Pol-Wort "Individual" (auf der W–B-Diagonale) verdeckte einen Teil des Ally-Themas "Progress" (auf der U–B-Kante), da beide bei der ursprünglichen Fünfeck-Größe aus Task 1.5 zu dicht beieinander lagen. Ein automatisierter Kollisionstest (`elementFromPoint` an allen 15 Label-Mittelpunkten, siehe Testkommentare) bestätigt danach: keine Beschriftung deckt eine andere ab. `pentagon.py`s bestehende Tests referenzieren `VERTEX_RADIUS` symbolisch, keine Zahl war fest verdrahtet.

### D-45 · Ziel/Mittel nur noch in der Info-Box, nicht mehr am Fünfeck
**Status:** Angenommen · 2026-09-09
Ziel und Mittel einer Einzelfarbe (`ColorCombination.goal`/`means`) stehen nicht mehr als zusätzliche Textzeile unter dem Vertex-Namen im Fünfeck. Stattdessen zeigt die Info-Box sie nur bei **1 selektierten Farbe**, als ein Satz "`goal` through `means`" (z. B. "peace through order"). `pentagon.py` verliert damit die gesamte Mehrzeilen-Logik aus Task 1.7 (`Vertex.label_lines()`/`bounds_with()` mit `extra_lines`) wieder — `Vertex.bounds` hängt jetzt nur noch von Dingen ab, die für jede Farbe *immer* gelten (Position, Symbolgröße, eigener Name), nie von der Selektion.
**Warum:** Sichtbarkeitstest durch die Nutzerin nach Task 1.7: Weil Ziel/Mittel nur bei 0 Farben gezeigt wurden, sprang das Fünfeck beim Wählen der ersten Farbe in Größe, Position und Namens-Schriftgröße (die `viewBox`-Berechnung berücksichtigte die zusätzlichen Zeilen). Die fünf Vertices sind unabhängig von der Selektion ohnehin immer alle da (nur ihre Hervorhebung ändert sich, FR-C6) — sie jetzt auch inhaltlich identisch zu rendern macht das Fünfeck über jede Selektionsgröße hinweg stabil. Ein Regressionstest (`test_the_pentagon_is_identical_across_selection_sizes`) vergleicht viewBox, Namens-Schriftgröße und Vertex-Positionen über 0/1/Ally/Enemy/3-Farben-Zustände. PRD §5.2 ist entsprechend angepasst: die "0 Farben"-Zeile verliert Ziel/Mittel, die "1 Farbe"-Zeile bekommt sie in der neuen Form dazu.

### D-46 · Wurzel-URL "/" leitet auf /colors/ weiter
**Status:** Angenommen · 2026-09-09
`config/urls.py` bekommt eine Route für `""`, die (temporär, 302) auf `colors:index` weiterleitet.
**Warum:** Beim Ausprobieren durch die Nutzerin gefunden: "/" selbst hatte noch nie eine eigene Seite (kein v0.1-Feature sieht das vor). `apps.core.gate.safe_next_url()` fällt aber genau auf "/" zurück, wann immer kein spezifisches Ziel angefragt wurde (z. B. ein direkter Aufruf der bloßen Startadresse) — nach erfolgreichem Login landete man dadurch auf einer 404-Seite statt bei den Color Infos. Temporär statt kanonisch (anders als die Redirects aus Task 1.6): "/" ist noch keine eigene Ressource, die sich später einmal ändern könnte, sobald Accounts oder Quiz eine echte Startseite brauchen — ein dauerhafter (301) Redirect würde das unnötig festschreiben.

### D-47 · HTMX braucht einen kleinen JS-Patch für SVG-`<a>`-Elemente
**Status:** Angenommen · 2026-09-09
`static/js/main.js` (neu, nach `htmx.min.js` in `base.html` eingebunden): ein einziger delegierter `click`-Listener, der `event.preventDefault()` aufruft, wenn das geklickte `<a hx-get>` ein `SVGAElement` ist.
**Warum:** Beim echten Browser-Test von Task 1.8 zeigte sich (per `pagehide`-Listener und doppeltem Request im Access-Log nachgewiesen): Klicks auf die Fünfeck-Ecken lösten einen vollständigen Seiten-Reload aus, keinen HTMX-Swap — trotz korrekt gesetzter `hx-get`/`hx-select`/`hx-target`-Attribute und geladenem HTMX. Ursache, im vendorten `htmx.min.js` selbst gefunden: HTMX entscheidet in seiner internen `shouldCancel()`-Funktion über `elt instanceof HTMLAnchorElement`, ob es die native Navigation per `preventDefault()` unterbindet. Die Fünfeck-Ecken sind `<a>` *innerhalb* eines `<svg>` (Task 1.5/1.6) — das macht sie zu `SVGAElement`, nie zu `HTMLAnchorElement`. HTMX feuerte deshalb zwar korrekt seinen eigenen AJAX-Request, ließ daneben aber den Browser dem `href` ganz normal folgen: zwei identische Requests, und der echte Seitenwechsel gewann. Der "Reset selection"-Link (ein normales HTML-`<a>` außerhalb des SVG) war nie betroffen. D-24s Grundsatz — echte Links, kein JS-Framework — bleibt unangetastet; das ist die kleinstmögliche Ergänzung, um eine bekannte Grenze von HTMX bei SVG-Inhalten auszugleichen, keine Abkehr vom Ansatz.
