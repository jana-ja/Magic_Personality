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
**Status:** Ersetzt durch D-60 · 2026-09-05
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

### D-48 · Programmatisches Klicken auf SVG-`<a>`-Elemente braucht ebenfalls einen Workaround
**Status:** Angenommen · 2026-09-09
`static/js/main.js` bekommt `simulateClick(element)`: ruft `element.click()` auf, wenn diese Methode existiert, sonst wird ein `MouseEvent("click")` manuell konstruiert und dispatcht. Task 1.9 nutzt das für die Tastaturkürzel W/U/B/R/G, Esc und die Leertaste — überall dort, wo main.js selbst einen Klick auf eine Fünfeck-Ecke auslöst, statt auf einen echten Klick zu reagieren.
**Warum:** Derselbe HTML/SVG-Unterschied wie D-47, diesmal an anderer Stelle: `SVGAElement` hat — anders als `HTMLAnchorElement` — gar keine `.click()`-Methode; sie ist eine HTML-spezifische Konvenienzmethode, kein Teil der allgemeinen DOM-`Element`-Schnittstelle. Ein naives `vertex.click()` wirft `TypeError: vertex.click is not a function` und bricht den Tastatur-Pfad vollständig ab (im Browser nachgewiesen: die Leertaste tat zunächst sichtbar gar nichts). Der Reset-Link ist ein echtes HTML-`<a>` und hätte `.click()` schon gehabt — `simulateClick()` behandelt ihn trotzdem einheitlich mit, damit an dieser Stelle nicht zwischen den beiden Elementtypen unterschieden werden muss.

### D-49 · Pol-/Theme-Labels bekommen eine eigene, großzügigere Zeichenbreiten-Konstante
**Status:** Angenommen · 2026-09-09
`pentagon._label_width()` (Pol- und Theme-Label-Pills, D-37) rechnete bislang mit derselben `NAME_CHAR_WIDTH` (0.62) wie `Vertex.bounds` für die Farbnamen am Fünfeck. Neu: eine eigene Konstante `LABEL_CHAR_WIDTH = 0.75`, nur für `_label_width()`.
**Warum:** `NAME_CHAR_WIDTH` ist an kurzen, aufrechten Farbnamen ("White", "Blue", …) kalibriert. Pol- und Theme-Labels sind aber kursiv bzw. fett gesetzt (`.pentagon__pole-label text` / `.pentagon__theme-label text` in `base.css`) und tragen mehrwortige Sätze wie "Short-sighted reacting" statt einzelner Namen — beides rendert im Schnitt breiter, als die gemeinsame Konstante annahm, und ließ nur wenig Luft zwischen geschätzter und tatsächlicher Textbreite. Eine Messung der echten Breite (SVG `getComputedTextLength()`, mit Kursiv-/Fettstil, System-UI-Font) über alle Pol- und Theme-Texte aus `seeds/colors_en.json` ergab als schmalste Reserve ~0,68 Zeichenbreiten je Schriftgröße (Wort "Good") — `LABEL_CHAR_WIDTH = 0.75` lässt dort noch gut 10 % Spielraum für andere Schriftarten/Browser, ohne die Pills unnötig aufzublasen. Ein Regressionstest (`apps/colors/tests/test_pentagon.py`) prüft für jeden Pol- und Theme-Text aus der echten Seed-Datei, dass die berechnete Box breiter bleibt als eine konservative Referenzbreite.

### D-50 · Produktions-Compose als dritte Datei statt in `compose.yaml` selbst
**Status:** Angenommen · 2026-09-14
`compose.yaml` (Task 0.3) enthält jetzt nur noch `db` und `web`, beide **ohne** Host-Ports. Zwei neue Dateien ergänzen das für den jeweiligen Zweck: `compose.override.yaml` (lokale Entwicklung — Host-Ports 5432/8000, `SECURE_SSL_REDIRECT=False`; wird von `docker compose` automatisch zusätzlich eingelesen, solange kein `-f` angegeben wird) und `compose.prod.yaml` (Server — fügt `caddy` hinzu, macht `db`/`web` mit `restart: unless-stopped` neu startfest, und setzt für `web` zusätzlich `image: ghcr.io/jana-ja/magic_personality:${IMAGE_TAG:-latest}`). Das Server-Deployment ruft compose explizit mit `-f compose.yaml -f compose.prod.yaml` auf (`docs/DEPLOYMENT.md`).
**Warum:** ARCHITECTURE.md §11.1 nennt "`compose.yaml` mit `web`, `db`, `caddy`" für die Produktion, D-30 legt für die *lokale* `compose.yaml` aber ausdrücklich nur `web` und `db` fest, ganz bewusst ohne Caddy/TLS-Aufwand. Eine einzelne Datei für beide Fälle hätte diesen Widerspruch nicht auflösen können; Docker Compose kann per Override-Datei zwar Werte *hinzufügen* oder *ersetzen*, aber keine Listeneinträge wie `ports:` durch bloßes Weglassen wieder *entfernen* — die Host-Port-Mappings mussten deshalb aus der Basis heraus in eine eigene, nur lokal geladene Datei wandern, nicht umgekehrt. Ohne Host-Port ist `web` in Produktion nur noch über Caddy erreichbar (`web:8000` im internen Compose-Netz) — das ist zugleich die Grundlage für D-51 und dafür, dass `/healthz` von außen nur über Caddy/TLS läuft (Task 1.12). Lokal per `docker compose config` gegengeprüft (Basis+Override ergibt exakt den bisherigen Dev-Aufbau) und per `docker compose -f compose.yaml -f compose.prod.yaml up -d` einmal real hochgefahren (Migrations-Schritt, Healthcheck, Gate — alle drei bestätigt, siehe D-52).

Das `image:` in `compose.prod.yaml` kam erst bei diesem realen Hochfahren dazu: `compose.yaml` hat für `web` nur `build: context: .` (für den lokalen Checkout gedacht) — ohne ein `image:` fand `docker compose pull` dort nichts zu pullen ("Skipped - No image to be pulled"), und `up -d` hätte einen vollständigen Checkout samt `Dockerfile` verlangt, den es auf dem Server laut `docs/DEPLOYMENT.md` bewusst nicht gibt. `IMAGE_TAG` (Default `latest`) macht ein Rollback auf einen älteren, von CI veröffentlichten Sha-Tag zu einer reinen `.env`-Änderung.

### D-51 · `client_ip()` vertraut X-Forwarded-For — nur weil "web" nie direkt erreichbar ist
**Status:** Angenommen · 2026-09-14
`apps/core/rate_limit.client_ip()` liest jetzt `X-Forwarded-For` (letzter Eintrag der Liste), fällt ohne den Header auf `REMOTE_ADDR` zurück.
**Warum:** Der ursprüngliche Kommentar (Task 0.5) verwies explizit auf Task 1.12: "muss angepasst und der Proxy als vertrauenswürdig konfiguriert werden". Mit D-50 veröffentlicht `compose.prod.yaml` für `web` keinen Host-Port mehr — jede Anfrage, die dort ankommt, ist also zwingend durch Caddy gelaufen, `REMOTE_ADDR` ist dort immer Caddys eigene Container-IP, nie die des echten Clients. Caddy *ergänzt* `X-Forwarded-For` um den von ihm selbst gesehenen Peer, statt einen vom Client mitgeschickten Wert zu ersetzen — ein Client könnte sich also durch einen eigenen, gefälschten `X-Forwarded-For`-Header eine andere IP vortäuschen, Caddys eigene Beobachtung steht aber immer als *letzter* Eintrag der Liste, deshalb zählt gezielt der. Ohne Caddy davor (lokale Entwicklung, Tests, `compose.override.yaml`) fehlt der Header komplett, `REMOTE_ADDR` bleibt dort unverändert die Quelle. Drei Regressionstests in `apps/core/tests/test_rate_limit.py`.

### D-52 · Produktions-Härtung in `config/settings/prod.py`: CSRF, Proxy-Header, HSTS, Healthcheck-Ausnahme
**Status:** Angenommen · 2026-09-14
Vier neue Einstellungen: `CSRF_TRUSTED_ORIGINS` (aus `ALLOWED_HOSTS` abgeleitet, `https://`-Präfix), `SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")`, `SECURE_HSTS_SECONDS` (env-gesteuert, Default 3600 = 1 Stunde, ohne Include-Subdomains/Preload) und `SECURE_REDIRECT_EXEMPT = [r"^healthz$"]`.
**Warum:** Alle vier wurden beim realen Durchspielen des Deployments sichtbar (Task 1.12), nicht am Schreibtisch erdacht:
- `manage.py check --deploy` warnte vor komplett fehlendem HSTS (`security.W004`) — der ursprüngliche Kommentar in `prod.py` hatte das seit Task 0.5 als offenen Punkt stehen lassen. 1 Stunde statt der oft empfohlenen ein bis zwei Jahre, weil sich HSTS im Browser-Cache nicht zurücknehmen lässt — ein Fehler im frischen Caddy/TLS-Aufbau würde sonst für die volle Dauer aussperren; nach ein paar Tagen unauffälligem Betrieb anheben (`docs/DEPLOYMENT.md`).
- Ohne `CSRF_TRUSTED_ORIGINS` lehnt Django jedes POST-Formular (Gate, später Login) über HTTPS ab — Django prüft den `Origin`-Header seit Version 4 gegen diese eigene Liste, `ALLOWED_HOSTS` allein reicht nicht mehr.
- Ohne `SECURE_PROXY_SSL_HEADER` hält Django jede Anfrage für unverschlüsselt, weil Caddy TLS terminiert und nur noch per HTTP an `web` weiterreicht (D-50) — `SECURE_SSL_REDIRECT` liefe dadurch in eine Endlosschleife.
- `SECURE_REDIRECT_EXEMPT` war der eigentliche Fund: Der Healthcheck aus `compose.yaml` prüft `web` *innerhalb* des eigenen Containers über reines HTTP an `localhost:8000` — nie über Caddy, also nie mit `X-Forwarded-Proto`. Lokal mit `docker compose -f compose.yaml -f compose.prod.yaml up` nachgestellt: Ohne diese Ausnahme leitete `SECURE_SSL_REDIRECT` auch diese interne Anfrage auf `https://` um, was am eigenen, unverschlüsselten Gunicorn-Socket mit einem SSL-Handshake-Fehler scheiterte — der Container blieb dauerhaft `unhealthy`. Betrifft nur den Redirect-Zwang für diesen einen Pfad, nicht die Erreichbarkeit von außen: Caddy erzwingt HTTPS an der eigenen Kante ohnehin schon.
Vier Regressionstests in `tests/test_prod_settings.py`, isoliert per `runpy.run_module()` (Djangos Settings lassen sich pro Prozess nur einmal konfigurieren, der reguläre Testlauf verwendet durchgehend `config.settings.dev`).

### D-53 · `seed_content` gehört fest in den Deployment-Ablauf, nicht nur in ARCHITECTURE.md §9
**Status:** Angenommen · 2026-09-16
`docs/DEPLOYMENT.md` führt `docker compose … run --rm web python manage.py seed_content --locale en` jetzt explizit als dritten Schritt zwischen `migrate` und `up -d` auf, sowohl beim ersten als auch bei jedem weiteren Deployment.
**Warum:** Auf dem echten Server reproduziert: Nach `migrate` allein lief die Seite scheinbar normal — Fünfeck, Navigation, die fünf Farbnamen waren da —, jede Auswahl zeigte aber nur leere Inhalte. Ursache, lokal mit einer frisch migrierten (aber nicht geseedeten) Datenbank nachgestellt: `apps/colors/migrations/0002_seed_colors_and_combinations.py` legt bewusst nur leere `ColorCombination`-Zeilen an ("noch ohne Inhalt", Kommentar im Migrationsfile selbst) — Namen, Ziel/Mittel, Eigenschaften, Perspektiven, Themes kommen ausschließlich über `seed_content` aus `seeds/colors_en.json` (ARCHITECTURE.md §9), stand dort aber nur als allgemeine Beschreibung des Content-Mechanismus, nicht als Deployment-Schritt. Die ursprüngliche `docs/DEPLOYMENT.md`-Fassung (Task 1.12) hatte das schlicht vergessen. Idempotent, deshalb ohne Risiko bei jedem Deployment erneut ausgeführt — Gegenprobe (`ColorCombination.objects.filter(name="").count() == 0`) jetzt mit im Fehlerbehebung-Abschnitt.

### D-54 · Task 2.6 vor Task 2.1 umgesetzt; `ColorAssignment.test_result` per Folgemigration ergänzt
**Status:** Angenommen · 2026-09-16
Roadmap-Reihenfolge abweichend umgesetzt: `quiz`s Fragebogen-Datenmodell (Task 2.6: `Questionnaire`, `Question`, `AnswerOption`, `TestResult`) entstand vor `accounts.Profile`/`ColorAssignment` (Task 2.1), obwohl die Roadmap Task 2.1 zuerst auflistet. Zusätzlich musste die Migration selbst aufgeteilt werden: `accounts/migrations/0002_…` legt `ColorAssignment` zunächst **ohne** das Feld `test_result` an; erst `accounts/migrations/0003_colorassignment_test_result.py` fügt es hinzu, nachdem `quiz/migrations/0001_initial.py` bereits gelaufen ist.
**Warum:** PRD §6.2 verlangt gegenseitige Fremdschlüssel zwischen den beiden Apps: `accounts.ColorAssignment.test_result` zeigt auf `quiz.TestResult` (D-07), `quiz.TestResult.profile` zeigt auf `accounts.Profile`. Beide Modelle existierten vor dieser Sitzung nicht — ein echter zyklischer App-Zusammenhang, den Djangos Migrations-Graph nicht als eine einzige, lineare Kette abbilden kann (`CircularDependencyError` beim ersten `migrate`-Versuch, mit automatisch erzeugten Migrationen, die sich gegenseitig über `('quiz', '__first__')` und `('accounts', '0002_…')` voraussetzten). Aufgelöst durch Reihenfolge **und** Aufteilung: zuerst `Profile` (ohne die Farbzuordnung) anlegen, dann das komplette Quiz-Modell (das jetzt auf ein existierendes `Profile` verweisen kann), zuletzt `ColorAssignment.test_result` in einer eigenen, dritten Migration ergänzen, die auf beide vorherigen Migrationen aufsetzt. Das Modell selbst entspricht weiterhin genau der Roadmap-DoD beider Tasks; nur die Reihenfolge der Umsetzung und die Migrationsdatei-Grenzen wurden angepasst, keine Architektur.

### D-55 · Kopfbereich bekommt Login-/Registrierungs-/Logout-Links
**Status:** Angenommen · 2026-09-17
`templates/base.html` zeigt im `site-header` jetzt rechts neben dem Logo entweder "Log in"/"Register" (nicht angemeldet) oder Nickname plus ein "Log out"-Formular (angemeldet). Neue Klassen `.site-header__auth` und `.form-errors` in `static/css/base.css`.
**Warum:** Task 2.2 (Roadmap) verlangt wörtlich nur die Mechanik von Registrierung/Login/Logout, nennt aber keine Stelle in der Navigation, von der aus man sie erreicht — ohne einen sichtbaren Einstiegspunkt wären die neuen Seiten nur über die direkte URL erreichbar, keine tatsächlich benutzbare Funktion. Der Kopfbereich ist die einzige Stelle, die auf jeder Seite dieser Anwendung sichtbar ist (`base.html`, seit Task 0.4), deshalb dort statt auf einer der Fachseiten. `user.profile.nickname` scheitert für einen Account ohne Profil (z. B. ein per `createsuperuser` angelegter Admin) still (Djangos Template-Engine behandelt `RelatedObjectDoesNotExist` als leeren String) — in v1 entstehen Profile aber ausschließlich zusammen mit dem User (Task 2.2s Registrierung selbst), das betrifft also nur Admin-Accounts außerhalb des reinen Nutzerflusses.

### D-56 · Profil-Bearbeitung: fünf Kontrollkästchen statt Fünfeck-Auswahl
**Status:** Angenommen · 2026-09-17
Das Formular unter `/accounts/profile/` (Task 2.4) wählt die eigenen Farben über fünf schlichte Checkboxen (White/Blue/Black/Red/Green), nicht über das SVG-Fünfeck aus `apps.colors`.
**Warum:** Die Fünfeck-Selektion (Task 1.6, D-24) steuert Navigation — jeder Klick wechselt die URL und zeigt sofort den zugehörigen Content an; es gibt dort keinen "Speichern"-Schritt und keinen Formular-Submit. Das Profil-Formular braucht aber genau das Gegenteil: mehrere Felder (Nickname, Bio, Farben) gemeinsam validieren und in einem POST speichern. Das Fünfeck für diesen Zweck nachzubauen (Klicks in versteckte Formularfelder übersetzen, eigene JS-Logik) wäre allein für diese eine Stelle deutlich mehr Aufwand als fünf `<input type="checkbox">` — und Task 2.4s DoD verlangt nur "1 bis 5 Farben frei wählbar", keine bestimmte Interaktionsform. Die serverseitige Menge wird wie überall sonst (D-27) auf `ColorCombination.code` abgebildet (`apps.colors.utils.canonical_code`), es gibt also weiterhin nur eine Darstellung von Farbmengen im System.

### D-57 · Avatar-Kreis über `border-radius`, nicht über SVG-`clipPath`
**Status:** Angenommen · 2026-09-17
Das generierte Profilbild (Task 2.5, `templates/accounts/_avatar.html`) ist eine quadratische `<svg viewBox="0 0 100 100">` mit vollflächigen, senkrechten `<rect>`-Streifen; der Kreis selbst entsteht über `border-radius: 50%; overflow: hidden;` auf dem `<svg>`-Element (`static/css/base.css`, `.avatar`), nicht über einen `<clipPath>` mit fester `id` innerhalb des SVGs.
**Warum:** Ein `<clipPath id="avatar-clip">` funktioniert für einen einzelnen Avatar auf einer Seite, bricht aber sobald dieselbe Vorlage mehrfach eingebunden wird — doppelte `id`-Werte sind ungültiges HTML, und `url(#avatar-clip)` trifft dann unvorhersagbar auf die erste Definition im Dokument. Genau dieser Fall kommt mit den Freundeslisten (Task 3.5) und der Suche (Task 3.2/3.3): mehrere Profile, und damit mehrere Avatare, auf derselben Seite. `border-radius` auf dem SVG-Wurzelelement selbst braucht keine `id`, ist beliebig oft wiederholbar und in allen unterstützten Browsern gleich zuverlässig.

### D-58 · Test durchführen: alle Fragen auf einer Seite, kein mehrschrittiger Assistent
**Status:** Angenommen · 2026-09-17
`/quiz/` (Task 2.8) zeigt alle Fragen der aktuell veröffentlichten Fragebogen-Version gleichzeitig in einem einzigen `<form>`, statt sie einzeln mit "Weiter"/"Zurück" durchzublättern. Fortschritt ("`x` of `n` answered") kommt als kleine, optionale JS-Ergänzung (`static/js/quiz.js`) obendrauf.
**Warum:** FR-T7 ("Zwischen den Fragen kann frei vor- und zurückgesprungen werden") ließe sich auch als mehrschrittiger Assistent mit Weiter/Zurück-Tasten lesen — das bräuchte aber zwingend clientseitigen JavaScript-Zustand, um beim Umblättern keine Antworten zu verlieren, *ohne* sie zwischenzeitlich zum Server zu schicken (FR-T8: "kein serverseitiger Zwischenstand"). Eine einzige Seite erfüllt beide Anforderungen bereits durch ihre Struktur: "vor- und zurückspringen" ist schlicht scrollen, nichts geht verloren, weil nichts jemals wegnavigiert wird — und das vollständig ohne eigenes JavaScript (ARCHITECTURE.md §4, Progressive Enhancement). FR-T9 ("alle Fragen müssen beantwortet sein") übernimmt dieselbe Mechanik wie das Registrierungsformular: `required`-Felder, serverseitig durch Djangos Formularvalidierung erzwungen, clientseitig zusätzlich durch natives HTML-Verhalten abgefangen. Die Fortschrittsanzeige selbst *ist* JavaScript-abhängig (ohne serverseitigen Zwischenstand lässt sich "wie viele sind schon beantwortet" anders nicht ermitteln) — das ist eine bewusste, kleine Ausnahme von "läuft auch ohne JS", betrifft aber nur eine Komfortanzeige, nicht die Funktionsfähigkeit selbst (die Seite bleibt ohne JavaScript vollständig ausfüllbar und abgebbar).

### D-59 · Zwei Randfälle der Auswertungsregel ausdrücklich festgelegt
**Status:** Angenommen · 2026-09-17
`apps/quiz/evaluation.py` (Task 2.9) legt zwei Fälle fest, die FR-T11/FR-T12 offenlassen: (1) Übersteuern `G(2)` und `G(4)` beide *und* sind exakt gleich groß, bleibt `k = 3` (der Standardwert) bestehen, statt eine der beiden Abweichungen willkürlich zu bevorzugen. (2) Ein Ergebnis mit nur einer Farbe ist über die spezifizierte Regel gar nicht erreichbar — `k` startet laut FR-T11 immer bei 2, 3 oder 4, und die Gleichstand-Erweiterung aus FR-T12 vergrößert `k` nur in Richtung 5, nie in Richtung 1. FR-T12 nennt trotzdem wörtlich "1 bis 5 Farben" als möglichen Ergebnisumfang.
**Warum:** (1) FR-T11.4 sagt nur "gewinnt der größere Abstand" — bei einem exakten Gleichstand zwischen den beiden Übersteuerungen selbst gibt es keinen größeren, die PRD nennt für diesen Fall keinen Sieger. Der Standardwert ist die neutralste verfügbare Antwort, keine neue Regel. (2) Das ist keine bewusste Entscheidung, sondern eine Beobachtung beim Testen (Roadmap 2.9 verlangt fünf tabellengetriebene Fälle, keiner davon ein Einzelfarben-Ergebnis) — durchgerechnet ergibt sich rechnerisch, dass `k=1` mit den gegebenen Schritten (Start bei 2/3/4, nur wachsende Gleichstand-Erweiterung) nie auftreten kann. Für die reale, ausbalancierte Fragebogen-Struktur aus FR-T3 (jede Farbe maximal 8 von 20 Punkten) ist das ohnehin unauffällig; hier nur dokumentiert, damit die Diskrepanz zur PRD-Formulierung nicht als übersehener Fehler missverstanden wird.

### D-60 · Fragebogen v1: 30 Fragen in drei Dimensionen statt 20 Fragen in vier
**Status:** Angenommen · 2026-09-17 · ersetzt D-16
Jedes der 10 Farbpaare kommt genau einmal je Dimension vor: **Handeln** (`ACTION`, das Mittel einer Farbe), **Antrieb** (`MOTIVATION`, ihr Ziel) und **Wahrnehmung** (`PERCEPTION`, was auffällt oder stört). Das ergibt 30 Fragen, jede Farbe erscheint in 12. Weiterhin 2 Antworten, 1 Punkt, versioniert. `Question.Dimension` entsprechend umgestellt (`quiz/migrations/0002`), die alten Werte `INNER`/`OUTER`/`FEELING`/`VALUES` entfallen.
**Warum:**
- Mit vier Dimensionen bei 20 Fragen war „alle Dimensionen sind vertreten“ schon mit einer Frage pro Dimension erfüllt, sicherte also nichts. Eine echte Balance je Farbe hätte jede Dimension in ein starres Muster gezwungen. „Innere Reaktion“ und „Gefühl“ ließen sich außerdem kaum trennen.
- Mittel und Ziel liegen für jede Farbe schon als Content vor (`goal`/`means`, Task 1.4). Zwei Menschen können gleich handeln, aber aus verschiedenen Gründen — gerade bei Ally-Paaren trennt die Antrieb-Frage besser. Wahrnehmung ergänzt einen dritten Blick, der über „was stört dich mehr“ auch das Problem sozialer Erwünschtheit abschwächt.
- Weil jede Dimension alle 10 Paare genau einmal enthält, bleibt die Balance erhalten, wenn eine Dimension später herausgefiltert wird (z. B. falls 30 Fragen sich als zu lang erweisen).
- Gefühle und Lebensbereiche sind keine gemessene Dimension mehr, sondern eine weiche Vorgabe für die Vielfalt der Situationen (Arbeit, Freundschaft, Wohnen, Freizeit …).

**Qualitätsregeln für die Fragen:**
1. Beide Antworten sind gleich attraktiv; jede zeigt eine Stärke ihrer Farbe, keine Schwäche.
2. Beide Antworten sind ähnlich lang und ähnlich konkret.
3. Bei Ally-Paaren geht es um den Unterschied, nicht um das Gemeinsame.
4. Keine erkennbaren Muster: jede Farbe steht gleich oft an erster Stelle, kein Paar hat immer dieselbe Reihenfolge, aufeinanderfolgende Fragen teilen keine Farbe.
5. Zwei Fragen desselben Paares schildern unabhängige Situationen. Farben werden nie benannt.
6. Sprache Englisch (NFR-4).

Regeln 2, 4 und 5 (soweit automatisch prüfbar) sichert `apps/quiz/tests/test_questionnaire_v1.py` gegen die echte Seed-Datei ab.
**Offen:** Bei 30 statt 20 Punkten ist ein Abstand von `T` = 2 (D-17) relativ kleiner. Nicht vorab geändert, sondern mit R-4 nach echten Durchläufen kalibrieren.

### D-61 · Übernahme ins Profil liest `TestResult.result_colors`, berechnet nicht neu
**Status:** Angenommen · 2026-09-17
`apps.quiz.views.adopt_result` (Task 2.10) übernimmt die schon in `TestResult.result_colors` gespeicherte Kombination unverändert, statt `evaluate_combination(test_result.scores)` erneut aufzurufen.
**Warum:** `QUIZ_RESULT_THRESHOLD` (Task 2.9) ist als Einstellung bewusst veränderlich (R-4: „T ist erst nach echten Durchläufen kalibrierbar“). Würde die Übernahme die Auswertungsregel zum Zeitpunkt des Klicks neu anwenden, könnte ein alter Testeintrag nach einer T-Anpassung ein anderes Ergebnis übernehmen, als er selbst je gezeigt hat — die Person würde Farben bestätigen, die sie nie gesehen hat. `result_colors` ist die einzige Quelle der Wahrheit für „was diese Person zu diesem Zeitpunkt als Ergebnis gesehen hat“.

### D-62 · Anonymes Testergebnis: signiertes Token in localStorage, globales Einlöse-Skript
**Status:** Angenommen · 2026-09-17
Ohne Login (Task 2.11) bekommt die Ergebnisseite ein von Django signiertes Token (`apps.quiz.anonymous_result`, dieselbe `signing.dumps`/`loads`-Technik wie das Gate-Cookie aus Task 0.5) mit `questionnaire_version` und `scores` — nicht dem fertigen Kombinationscode. `static/js/quiz_claim.js` legt es in `localStorage` ab und lädt in `base.html` auf **jeder** Seite; ist der Body als `data-authenticated="true"` markiert und liegt ein Token vor, baut es einen unsichtbaren Formular-POST an `/quiz/results/claim/` und schickt ihn sofort ab. Der Server prüft Signatur und Alter (`QUIZ_ANONYMOUS_RESULT_MAX_AGE`, eine Woche) und verwirft alles andere kommentarlos.
**Warum:**
- **Warum die Punktzahlen signieren statt des fertigen Ergebnisses:** Die Auswertungsregel (Task 2.9) wird beim Einlösen ganz regulär auf die Punktzahlen angewendet, mit den *dann* gültigen Einstellungen — im Unterschied zu D-61 (Übernahme ins Profil), wo das Ergebnis dem Menschen zum Testzeitpunkt schon gezeigt wurde. Hier wird es dem Menschen zum ersten Mal *als Historieneintrag* gezeigt, genau beim Einlösen — es gibt keinen früheren angezeigten Stand, der sich verändern könnte.
- **Warum kein bestimmtes Ziel für Login/Registrierung:** `LOGIN_REDIRECT_URL` zeigt auf die öffentliche Fünfeck-Seite, nicht auf eine feste "nach dem Test"-Route. Ein Skript, das auf jeder Seite nachschaut, statt eine Sonderbehandlung in die Login-/Registrierungs-Views einzubauen, funktioniert unabhängig davon, wo die Person tatsächlich landet — und bleibt bei künftigen Änderungen an diesen Zielen automatisch richtig.
- **Warum Signieren statt einer eigenen Zusatzprüfung reicht:** `django.core.signing` verhindert Manipulation kryptographisch (jede Änderung am Token macht die Signatur ungültig); `max_age` deckt "veraltet" ab. `anonymous_result.unsign()` prüft zusätzlich die Form der Punktzahlen (genau die fünf Farbcodes, keine negativen Werte) als zweite, günstige Absicherung — nicht weil die Signatur das nicht schon abdeckt, sondern falls sich das Tokenformat einmal ändert.
- **Bewusst nicht behandelt:** Ein Token doppelt einzulösen (z. B. zwei gleichzeitig offene Tabs) ist rechnerisch möglich, seit `localStorage.removeItem()` im Skript unmittelbar vor dem Absenden läuft aber nur bei einer echten Race Condition erreichbar — bei 3–10 Nutzenden nicht der Aufwand einer eigenen Idempotenz-Sperre wert. Im schlimmsten Fall entsteht ein doppelter, selbst löschbarer Historieneintrag (Task 2.12).

### D-63 · Backups: Cron-Skript statt viertem Container, Docker-Volume statt Host-Pfad
**Status:** Angenommen · 2026-09-17
`scripts/backup.sh` (Task 2.14) läuft über einen Cron-Eintrag auf dem Server selbst, nicht in einem eigenen Backup-Container, und schreibt `pg_dump`-Ausgaben in ein eigenes, benanntes Docker-Volume (`postgres_backups`, `compose.prod.yaml`), nicht auf einen Host-Pfad. Die Wiederherstellung selbst bleibt bewusst ein dokumentiertes Runbook in `docs/DEPLOYMENT.md`, kein Skript — und verlangt darin ausdrücklich, ein Backup zuerst gegen eine Wegwerf-Datenbank zu prüfen, bevor die echte ersetzt wird.
**Warum:**
- **Kein vierter Container:** ARCHITECTURE.md §2 legt die Container-Topologie ausdrücklich auf drei fest (`web`, `db`, `caddy`) — ein zusätzlicher, dauerhaft laufender Backup-Dienst (z. B. ein populäres `postgres-backup`-Image mit eingebautem Cron) würde diese bewusst kleine Fläche wieder vergrößern, für eine Aufgabe, die ein einzeiliger Host-Cron-Eintrag plus ein kurzes Skript genauso gut erledigt.
- **Docker-Volume statt Host-Pfad:** ARCHITECTURE.md §11.4 nennt wörtlich "in ein Volume". Ein Docker-Volume bleibt unabhängig davon funktionsfähig, wo `docker compose` gerade ausgeführt wird, und vermeidet Datei-Berechtigungsprobleme zwischen Host-Nutzer und dem `postgres`-Prozess im Container (der intern als eigener, containerinterner Nutzer läuft).
- **Kein Restore-Skript:** Ein Backup läuft automatisiert und folgenlos — schlägt es fehl, gibt es morgen ein neues. Eine Wiederherstellung ersetzt im Ernstfall die einzige Datenbank der Anwendung; das verdient jedes Mal eine bewusste, im Moment getroffene Entscheidung (welches Backup, welche Zieldatenbank), keine Automatisierung, die im Zweifel zu leicht auf die falsche Datenbank zeigen könnte.
- **Erst gegen eine Wegwerf-Datenbank, dann erst gegen die echte:** Genau der Fehler, den ein Restore-Runbook verhindern soll, wäre ein beschädigter oder unvollständiger Dump, der erst beim Ersetzen der echten Datenbank auffällt — dann ist es zu spät. Die Probe gegen `restore_check` (dieselbe Technik wie die hier tatsächlich durchgeführte Generalprobe) kostet nur wenige Sekunden und macht genau das unmöglich.

### D-64 · Hauptnavigation im Kopfbereich statt Einstieg auf der Farbseite
**Status:** Angenommen · 2026-09-17
`templates/base.html` zeigt neben dem Projektnamen eine `<nav class="site-nav">` mit „Colors“ und „Personality Test“ (Task 2.15). Der aktive Bereich ergibt sich aus `request.resolver_match.app_name` und wird per `aria-current="page"` markiert, zusätzlich fett und unterstrichen (NFR-6). Rechts bleibt der Account-Bereich aus D-55 unverändert.
**Warum:**
- Nach dem Deployment von v0.2 war der Test nur über die direkte URL erreichbar. Keine Aufgabe hatte einen Einstieg vorgesehen, genauso wie zuvor bei Login/Registrierung (D-55).
- Der Kopfbereich ist die einzige Stelle, die auf jeder Seite sichtbar ist. Ein Button nur auf `/colors/` hätte den Test von Profil-, About- oder Ergebnisseiten aus nicht erreichbar gemacht.
- Bewusst nur zwei Punkte: Das Profil ist über den Nickname rechts schon erreichbar. Ein weiterer Punkt kommt erst mit der Profilsuche (v1.0) dazu.
- Mobil reicht bei zwei kurzen Links ein Zeilenumbruch (`flex-wrap`) unter dem Projektnamen; ein Hamburger-Menü bräuchte JavaScript und brächte bei zwei Einträgen nichts.
