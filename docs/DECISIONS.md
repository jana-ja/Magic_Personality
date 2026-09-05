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
