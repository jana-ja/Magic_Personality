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
- Keine Moderationswerkzeuge über das Melden von Beiträgen und Kommentaren und das Django-Admin hinaus (kleiner, persönlich bekannter Nutzerkreis; ab v1.3, FR-B10).
- Kein Social Login, kein Newsletter, keine Benachrichtigungen per E-Mail oder Push. Ab v1.4 zeigt die Seite selbst einen Zähler neuer Kommentare (FR-B20).

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

### v1.1 — Nachbesserungen aus der Nutzung
Fehlerbehebungen und kleine Ergänzungen nach v1.0 (Such-Link in der Navigation, Punkte des übernommenen Testergebnisses im fremden Profil, Übernahme aus der Historie, Django-Admin, Sprache nur Englisch, kein Überschreiben unveränderter Farben beim Speichern).

### v1.2 — Profil-Überarbeitung
Ein Profil für eigene und fremde Ansicht, Kopfbereich mit Farbbanner, Tabs, Sidebar mit Kurzinfos, einzeln bearbeitbare Bereiche und eine wiederverwendbare Autorenkarte. Bereitet Blogbeiträge und Kommentare zu Farben vor (§8.2), die später den meisten Platz auf der Seite bekommen.

### v1.2.1 — Feedback zum Test
Ein kleines Formular, mit dem Testende Rückmeldung zum Personality Test geben: direkt auf der Ergebnisseite und dauerhaft über einen Link im Footer (für alle, die den Test schon vorher gemacht haben). Anonym, in der Datenbank gespeichert. Übt nebenbei, wie Nutzereingaben abgesichert werden, bevor Blogbeiträge und Kommentare sie für andere sichtbar machen.

### v1.3 — Beiträge
Registrierte Nutzende schreiben Beiträge, optional mit einer Farbkombination verknüpft. Sie erscheinen im Profil (Tab „Posts") und in den Color Infos unter den Eigenschaften der gewählten Kombination. Beitragsseite, Markdown, Bearbeiten, Löschen und Melden. Alles zunächst für alle Angemeldeten sichtbar; ein Sichtbarkeitsfeld für „nur Freunde" ist vorbereitet.

### v1.4 — Kommentare
Kommentare unter Beiträgen, flach mit festen Nummern (#3) und Antwort-Verweisen, Tab „Comments" im Profil, Melden auch für Kommentare, ein Zähler neuer Kommentare und Antworten für die eigene Person.

### v1.5 — Pinnwand
Beiträge und Kommentare (eigene und fremde) an die eigene Pinnwand heften. Ersetzt den „Coming soon"-Platzhalter aus v1.2.

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
| **0 Farben** | Auf jeder Ally-Kante deren gemeinsames Anliegen; an beiden Enden jeder Feind-Diagonale die neutrale Sicht auf diesen Konflikt. Das Fünfeck selbst ist dabei identisch zu jedem anderen Selektionszustand (Größe, Position, Namens-Schriftgröße) — Ziel und Mittel stehen nicht mehr an der Ecke, sondern nur noch in der Info-Box bei 1 Farbe (D-45) |
| **1 Farbe** | Name · Ziel und Mittel als ein Satz ("`goal` through `means`", D-45) · Guiding Question · Eigenschaften (center, sowie in einer Zeile unterhalb von Fünfeck und Info-Box nach dem jeweiligen Nachbarn gruppiert — links/rechts folgt der Bildschirmposition, nicht der WUBRG-Reihenfolge) · die beiden Ally- und die beiden Enemy-Farben, benannt (D-40). Am Fünfeck tragen die beiden Feind-Diagonalen statt der neutralen Sicht die **eigene** Sicht dieser Farbe, an beiden Enden |
| **2 Farben** | Beziehungstyp (Ally / Enemy) · Name · Guiding Question · Archetype · bei **Ally**: Eigenschaften (eine Eigenschaften-Zeile ohne Links/Rechts-Aufteilung, die Traits eines Paares tendieren zu keinem Nachbarn) sowie der gemeinsame Feind und die neutrale Sicht auf den Konflikt der beiden übrigen Nachbarn ("Neighbour ally conflict", D-40) · bei **Enemy**: alle drei Perspektiven (A über B, B über A, neutral). Am Fünfeck zusätzlich das gemeinsame Wort des Paares auf seiner Linie |
| **3–5 Farben** | Name |

Die Info-Box ist unabhängig von der Selektionsgröße immer sichtbar,
auch bei 0 Farben (dort mit einem Platzhaltertext) — ein reservierter
Bereich, damit die Seite beim Wählen der ersten Farbe nicht layoutmäßig
springt (D-41, ersetzt eine Task-1.6-Festlegung).

**Beschriftung der Linien am Fünfeck**

Nicht jede Linie trägt in jedem Zustand eine Beschriftung. Die Ecken
zeigen immer Ziel und Mittel; die Linien folgen dieser Tabelle
(Referenzzeichnungen: `docs/reference/`):

| Selektion | Ally-Kanten mit Wort des Paares | Feind-Diagonalen mit Pol-Wörtern an beiden Enden | ohne Beschriftung |
|---|---|---|---|
| **0 Farben** | alle fünf | alle fünf, neutrale Sicht | — |
| **1 Farbe X** | die beiden an X | die beiden an X, **aus X' eigener Sicht** | alle übrigen |
| **2 Ally X+Y** | X–Y sowie die zweite Kante von X und die von Y | X und Y je zum **gemeinsamen** Feind, aus eigener Sicht; dazu die Diagonale zwischen den beiden übrigen Feinden, neutrale Sicht | X und Y zu ihrem jeweils **anderen** Feind |
| **2 Enemy X+Y** | — | nur X–Y, neutrale Sicht, plus das Wort des Paares auf der Linie | alle übrigen |
| **3–5 Farben** | noch offen (FR-C11) | noch offen (FR-C11) | — |

Der Ally-Fall folgt derselben Logik wie der Artikel: Was ein
verbündetes Paar teilt, zeigt sich an seinem **gemeinsamen** Feind —
deshalb dort die eigene Sicht beider Farben. Wo das Paar auseinander
zieht, zeigt sich an den beiden **übrigen** Feinden und der Achse
zwischen ihnen. Die zwei Konflikte, die nur je eine der beiden Farben
betreffen, gehören zu keiner der beiden Aussagen und bleiben leer.

- **FR-C9** Ally/Enemy wird aus der Nachbarschaft im Farbrad **berechnet**, nicht gespeichert.
- **FR-C10** Eigenschaften werden nach Typ (Strength / Weakness / Neutral) unterschieden. Die Unterscheidung wird **nicht allein farblich** kodiert (siehe NFR-6).
- **FR-C11** Fehlender Content (z. B. Eigenschaften einer 3er-Kombination) führt zu einem leeren, aber fehlerfreien Bereich — nicht zu einem Fehler oder einer leeren Seite.

**v0.2-Ergänzung**
- **FR-C12** Eingeloggte Nutzende mit hinterlegten Farben sehen einen Button „Meine Farben auswählen", der die Selektion entsprechend setzt.

### 5.3 Personality Test (v0.2)

**Aufbau**
- **FR-T1** Der Fragebogen besteht ab Version 2 aus **15 Fragen mit je 5 Antwortmöglichkeiten**, eine je Farbe (D-65). Version 1 (30 Fragen mit je 2 Antworten, D-60) bleibt für bestehende Ergebnisse gültig.
- **FR-T2** Jede Frage stellt eine Situation dar und bietet fünf typische Reaktionen an, je eine pro Farbe. Die Zuordnung Antwort → Farbe ist für Testende nicht offensichtlich benannt; die Reihenfolge der Antworten folgt nicht der Farbe.
- **FR-T3** Testende wählen je Frage die Antwort, die **am besten**, und die, die **am zweitbesten** passt. Jede Farbe steht in jeder Frage zur Auswahl (max. 30 Punkte je Farbe, 45 Punkte gesamt).
- **FR-T4** Jede Frage gehört zu genau einer von drei Dimensionen: **Handeln** (wie man vorgeht, Mittel der Farbe), **Antrieb** (worum es einem geht, Ziel der Farbe) und **Wahrnehmung** (was einem auffällt oder einen stört). Jede Dimension hat gleich viele Fragen (5).
- **FR-T5** Die beste Antwort gibt ihrer Farbe **2 Punkte**, die zweitbeste **1 Punkt**. Die Punkte je Rang sind Teil der Fragebogen-Version (in v1: eine Antwort, 1 Punkt).
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
  5. `T` ist ein Schwellenwert **je Fragebogen-Version**, weil er von der Punkteskala abhängt: v1 **2 Punkte**, v2 **4 Punkte** (D-65). `T` ist so gewählt, dass Abweichungen von 3 Farben selten sind.
- **FR-T12** Punktgleichstand an der Schnittgrenze: Alle punktgleichen Farben werden aufgenommen. Das Ergebnis kann dadurch 1 bis 5 Farben umfassen.
- **FR-T13** Das Ergebnis nennt die resultierende Farbkombination mit ihrem Namen und verlinkt auf die zugehörige Ansicht in den Color Infos. Zusätzlich werden die Punktzahlen aller fünf Farben gezeigt.

**Nach dem Test**
- **FR-T14** *Eingeloggt:* Das Ergebnis wird automatisch in der Testhistorie gespeichert. Zusätzlich wird angeboten, es als Profilfarben zu übernehmen — verpflichtend ist das nicht.
- **FR-T15** *Nicht eingeloggt:* Das Ergebnis wird lokal im Browser (`localStorage`) zwischengespeichert und zur Registrierung eingeladen.
- **FR-T16** Meldet sich ein Gast anschließend an oder registriert sich, wird ein zwischengespeichertes Ergebnis wie unter FR-T14 behandelt (Historie + Angebot zur Übernahme) und der lokale Zwischenspeicher geleert.
- **FR-T17** Der Test kann beliebig oft wiederholt werden. Jeder Durchlauf erzeugt einen eigenen Historieneintrag.

**Feedback (v1.2.1)**
- **FR-T18** Testende können Feedback zum Test geben: eine optionale **Bewertung von 1 bis 5** („Passt das Ergebnis zu dir?") und einen optionalen **Freitext** (höchstens 2000 Zeichen); mindestens eines von beiden ist nötig. Das Formular steht auf der Ergebnisseite und unter `/feedback/`, erreichbar über den Footer jeder Seite.
- **FR-T19** Feedback ist **anonym**: mit oder ohne Login abgebbar, ohne Verweis auf Account, Profil oder IP-Adresse. Gespeichert werden Bewertung, Text, Zeitpunkt und — wenn direkt nach einem Test abgegeben — die Fragebogen-Version. Feedback überlebt die Account-Löschung (FR-U8), weil es nicht zugeordnet ist.
- **FR-T20** Absendungen sind je IP-Adresse begrenzt (5 pro Stunde). Feedback ist nur für die Projektinhaberin im Django-Admin sichtbar, niemals für andere Nutzende.

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

### 5.5.1 Profil-Überarbeitung (v1.2)

- **FR-P9** Eigenes und fremdes Profil sind **dieselbe Seite** unter `/u/<nickname>/`. Nur für die eigene Person kommen Bearbeiten-Knöpfe und private Bereiche hinzu; `/accounts/profile/` führt dorthin weiter.
- **FR-P10** Der **Kopfbereich** zeigt ein Banner aus den Profilfarben (gleichbreite Streifen in WUBRG-Reihenfolge wie beim Profilbild, neutral ohne Farben), Profilbild, Nickname, Kombinationsname und die passende Freundschaftsaktion.
- **FR-P11** Unterhalb des Kopfes stehen **Tabs** als echte Links: **Pinnwand** (Standardtab) und Freunde für alle, Testhistorie und Einstellungen nur für die eigene Person. Tabs für Beiträge und Kommentare kommen erst mit diesen Inhalten; die Pinnwand ist von Anfang an in der Leiste und zeigt bis dahin einen „Coming soon"-Platzhalter. Die privaten Adressen (Testhistorie, Einstellungen, Bearbeiten) führen für jede andere Person auf das Profil der Person aus der Adresse weiter.
- **FR-P12** Nickname, Bio und Farben sind **einzeln bearbeitbar**; jeder Bereich hat ein eigenes Formular und speichert ausschließlich seine eigenen Daten. Unveränderte Angaben werden nie überschrieben.
- **FR-P13** Farben werden entweder **aus einem Testergebnis der Historie übernommen** oder **manuell am Fünfeck** gewählt (1 bis 5); ohne JavaScript bleiben Kontrollkästchen.
- **FR-P14** Die **Sidebar** zeigt Bio, Farben samt Punkten des verknüpften Testergebnisses (D-70) und eine Freundesvorschau. Der Hauptbereich ist die **Pinnwand** (siehe §8.2), bis zu ihrer Umsetzung ein „Coming soon"-Platzhalter.
- **FR-P15** Eine **Autorenkarte** (Profilbild, Nickname, Kombination) ist eine wiederverwendbare Komponente; sie steht in Freundeslisten und Suchergebnissen und später neben Beiträgen und Kommentaren.
- **FR-P16** Die Seite hat ein eigenständiges **Mobil-Layout** (NFR-3): Sidebar unter dem Hauptbereich, Tabs umbrechen, kein horizontales Scrollen bei 375 px.

### 5.6 Social (v1.0)

- **FR-S1** Profile anderer sind **nur für eingeloggte Nutzende** sichtbar und zeigen: Nickname, Profilbild, Bio, Farben, Freundesliste. Nicht: Testhistorie, E-Mail.
- **FR-S2** Suche nach Nickname (Teilstring, case-insensitiv).
- **FR-S3** Suche nach Farbkombination: Ergebnis sind alle Profile, deren Farben die gesuchte Kombination **enthalten**. *(Suche „White" liefert auch WU und WB; Suche „WU" liefert auch WUB.)*
- **FR-S4** Freundschaften sind **beidseitig**: Anfrage senden, annehmen, ablehnen, bestehende Freundschaft auflösen. Offene Anfragen sind im eigenen Profil einsehbar.
- **FR-S5** Die eigene Freundesliste ist im eigenen Profil sichtbar.
- **FR-S6** Von einem Profil aus ist dessen Freundesliste einsehbar und deren Einträge sind navigierbar — der soziale Graph ist erkundbar.

### 5.7 Beiträge, Kommentare, Pinnwand (v1.3 bis v1.5)

Gestaltung und Begründung: D-78 bis D-82.

**Beiträge (v1.3)**
- **FR-B1** Registrierte Nutzende schreiben **Beiträge** mit Titel (höchstens 120 Zeichen) und Text (Markdown, höchstens 10 000 Zeichen). Jeder Beitrag gehört einem Profil; die Autorin bzw. der Autor ist überall sichtbar, wo der Beitrag steht (Autorenkarte, FR-P15).
- **FR-B2** Ein Beitrag ist optional mit **einer Farbkombination** (1 bis 5 Farben) verknüpft; ohne Farbe ist er allgemein. Die Wahl geschieht wie bei den Profilfarben am Fünfeck, ohne JavaScript mit Kontrollkästchen (FR-P13).
- **FR-B3** Markdown umfasst Überschriften, fett und kursiv, Listen, Zitate, Code und Links. **Kein** HTML, keine Bilder, keine Tabellen. Links nur mit `http`/`https`, jeder Link mit `rel="nofollow noopener noreferrer"`. Der Editor bietet eine Vorschau.
- **FR-B4** Die Autorin bzw. der Autor kann den eigenen Beitrag **bearbeiten** (Titel, Text, Farben) und **löschen**. Ein geänderter Beitrag trägt „edited" mit Zeitpunkt; unveränderte Angaben lösen keine Änderung aus. Löschen verlangt eine Bestätigung und entfernt Kommentare, Pins und Meldungen zu diesem Beitrag mit.
- **FR-B5** Jeder Beitrag hat eine **eigene Seite** (`/posts/<id>/`) mit Autorenkarte, Farbkombination (verlinkt auf die Color Infos), Datum und gerendertem Text.
- **FR-B6** Profil-Tab **Posts**: alle Beiträge der Person untereinander, neueste zuerst, mit Seiteneinteilung. Jeder Eintrag zeigt Titel, Farbkombination, Datum und einen Klartext-Auszug (etwa 200 Zeichen) und ist als Ganzes anklickbar. Die eigene Person sieht zusätzlich „Write a post".
- **FR-B7** Ist in den **Color Infos** eine Kombination gewählt, zeigt die Seite unterhalb der Eigenschaften ein **Grid** der Beiträge, die **genau** mit dieser Kombination verknüpft sind (kein Teilmengen-Treffer): neueste zuerst, höchstens 6, Link auf alle. Jede Karte zeigt Titel, Autorenkarte, Auszug (höhenbegrenzt) und Datum und ist als Ganzes anklickbar. Ohne gewählte Farben zeigt die Seite kein Grid. Ein Link „Write a post about this" öffnet den Editor mit vorbelegten Farben.
- **FR-B8** Beiträge und Kommentare sind **nur für eingeloggte Nutzende** sichtbar, auf jedem Pfad. Gäste sehen in den Color Infos statt des Grids nur einen Hinweis zum Anmelden.
- **FR-B9** Jeder Beitrag trägt ein Feld `visibility` mit dem einzigen Wert `public`. Jeder lesende Zugriff geht durch **eine** zentrale Sichtbarkeitsprüfung, damit „nur Freunde" (§8.2) später an einer Stelle ergänzt werden kann.
- **FR-B10** Jede Person kann fremde Beiträge (ab v1.4 auch Kommentare) **melden**: einmal je Person und Eintrag, mit optionalem Grund (höchstens 500 Zeichen). Meldungen sind nur im Django-Admin sichtbar; es gibt kein automatisches Ausblenden. Die Projektinhaberin löscht Beiträge dort bzw. entfernt Kommentare (FR-B16).
- **FR-B11** Schreiben und Melden sind **je Person** begrenzt (NFR-8): 30 Beiträge und 20 Meldungen pro Stunde.
- **FR-B12** Die Account-Löschung (FR-U8) entfernt die Beiträge der Person samt allem, was an ihnen hängt, sowie ihre eigenen Meldungen.

**Kommentare (v1.4)**
- **FR-B13** Unter einem Beitrag stehen **Kommentare**: Klartext (höchstens 2000 Zeichen) mit Zeilenumbrüchen und erkannten Links, **flach** und älteste zuerst. Die Autorin bzw. der Autor ist bei jedem Kommentar sichtbar (Autorenkarte, klein).
- **FR-B14** Jeder Kommentar trägt eine **Nummer je Beitrag** (`#1`, `#2`, …). Sie wird beim Anlegen vergeben und **nie neu vergeben**, auch nicht, wenn Kommentare gelöscht werden.
- **FR-B15** Ein Kommentar kann auf einen anderen Kommentar **desselben Beitrags antworten**. Die Antwort trägt den Verweis „↪ #3", der zum Bezug springt; Antworten werden nicht verschachtelt. Auf einen gelöschten Kommentar lässt sich nicht antworten.
- **FR-B16** Die Autorin bzw. der Autor kann eigene Kommentare **löschen**; Kommentare sind **nicht bearbeitbar**. Ein gelöschter Kommentar, auf den geantwortet wurde, bleibt als Hülle „deleted" mit Nummer (ohne Text und ohne Autor) stehen, damit Verweise und Nummern erhalten bleiben; eine Hülle ohne Antworten wird nicht angezeigt. Dasselbe tut die Projektinhaberin im Admin mit gemeldeten Kommentaren.
- **FR-B17** Profil-Tab **Comments**: alle Kommentare der Person (ohne Hüllen), neueste zuerst, mit Auszug, Nummer, Titel des Beitrags und Sprung zum Kommentar.
- **FR-B18** Kommentare lassen sich melden (FR-B10). Je Person sind 60 Kommentare pro Stunde erlaubt; Meldungen zählen gemeinsam (FR-B11).
- **FR-B19** Die Account-Löschung macht die Kommentare der Person unter fremden Beiträgen zu Hüllen (FR-B16); an eigenen Beiträgen verschwinden sie mit dem Beitrag.
- **FR-B20** Die eigene Person sieht am Tab „Posts" einen **Zähler neuer Kommentare** unter eigenen Beiträgen und neuer Antworten auf eigene Kommentare (jeweils von anderen), gezählt seit die Beitragsseite zuletzt geöffnet wurde. Betroffene Einträge in den Tabs „Posts" und „Comments" sind markiert. Der Zähler steht nur im eigenen Profil; es gibt keine E-Mail, keinen Push und keine Benachrichtigungsliste.

**Pinnwand (v1.5)**
- **FR-B21** Jede Person kann Beiträge und Kommentare, **eigene und fremde**, an die eigene **Pinnwand** heften und wieder lösen; ein Eintrag höchstens einmal.
- **FR-B22** Der Tab **Pinnwand** zeigt die gepinnten Einträge, zuletzt gepinnte zuerst, für alle Angemeldeten sichtbar. Jeder Eintrag zeigt die **Autorenkarte des Originals** (nicht der pinnenden Person), Art (Beitrag/Kommentar), Auszug und Link zum Original. Das ersetzt den „Coming soon"-Platzhalter (FR-P14).
- **FR-B23** Ein Pin ist ein **Verweis**: nichts wird kopiert. Er verschwindet, wenn das Original gelöscht wird oder zur Hülle wird, und er wird nicht gezeigt, wenn die ansehende Person das Original nicht sehen darf (FR-B9).
- **FR-B24** Fremde Autorinnen und Autoren müssen der Aufnahme nicht zustimmen: Die Inhalte sind ohnehin für alle Angemeldeten sichtbar, ein Pin macht sie nicht sichtbarer.

---

## 6. Datenmodell

### 6.1 Content

**`Color`** — die fünf Farben als feste Stammdaten
`code` (W/U/B/R/G) · `name` · `symbol` · `hex` · `wheel_position` (0–4, im Uhrzeigersinn ab White)

**`ColorCombination`** — alle **31** Kombinationen, vollständig vorangelegt
`colors` (Menge, 1–5) · `name` · `goal` · `means` · `guiding_question` · `archetype` · `theme` · `locale`

> `theme` ist das eine Wort, das im Fünfeck auf der Linie zwischen zwei Farben steht — bei einem Ally-Paar ihr gemeinsames Anliegen, bei einem Feindpaar das, was beide zusammen ergeben. `goal` und `means` sind bewusst je ein Wort: sie stehen an der Fünfeck-Ecke.

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
`version` · `question_count` · `published_at` · `choice_points` (Punkte je Rang, z. B. `[2, 1]`) · `result_threshold` (`T`)

**`Question`** / **`AnswerOption`**
`questionnaire` · `position` · `text` · `dimension` (ACTION / MOTIVATION / PERCEPTION) · `locale`
je Option: `position` · `text` · `color` · `locale`

**`TestResult`** — Historieneintrag
`profile` · `questionnaire_version` · `taken_at` · `scores` (Punkte je Farbe) · `result_colors`

**`Friendship`**
`profile_a` · `profile_b` · `status` (PENDING / ACCEPTED) · `requested_by` · `created_at`

> Verweist auf `Profile`, nicht auf `User` — damit später auch fremd angelegte Profile Teil des Graphen sein können.

**`Post`** — Beitrag (v1.3)
`author` (Profile) · `title` · `body` (Markdown) · `colors` (kanonischer Code, leer = allgemein) · `visibility` (`public`) · `created_at` · `edited_at` · `comment_seq` (Zähler für Kommentarnummern)

**`Comment`** — Kommentar (v1.4)
`post` · `author` (Profile, leer bei einer Hülle nach Account-Löschung) · `number` (je Beitrag eindeutig) · `body` (Klartext) · `reply_to` (Comment, optional) · `created_at` · `deleted_at`

**`Report`** — Meldung (v1.3, um Kommentare erweitert in v1.4)
`reporter` (Profile) · `post` **oder** `comment` · `reason` · `created_at` · `handled_at`

**`PostSeen`** — Stand des Zählers (v1.4)
`profile` · `post` · `last_seen_number`

**`Pin`** — Pinnwand-Eintrag (v1.5)
`profile` · `post` **oder** `comment` · `created_at`

> Beitrag und Kommentar verweisen auf `Profile`, nicht auf `User`, wie `Friendship`: die Autorenkarte braucht nur das Profil, und fremd angelegte Profile (§8.1) bleiben möglich. Die Farbverknüpfung ist ein kanonischer Code wie bei `TestResult.result_colors`, kein Fremdschlüssel auf `ColorCombination` (die ist an eine Sprache gebunden).

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
- **Pinnwand** im Profil: ab v1.5 umgesetzt (FR-B21 bis FR-B24). Ein Pinnwand-Eintrag verweist auf einen Beitrag oder Kommentar beliebiger Autorschaft und kopiert nichts.
- **Sichtbarkeit „nur Freunde"** für Beiträge: das Feld `visibility` und die zentrale Sichtbarkeitsprüfung sind vorbereitet (FR-B9). Noch zu entscheiden, wenn es kommt: ob Kommentare der Sichtbarkeit ihres Beitrags folgen (Vorschlag: ja), Verhalten von Pins auf danach eingeschränkte Beiträge (Vorschlag: ausgeblendet, FR-B23), Umstellung bestehender Beiträge.
- Später denkbar, jetzt bewusst nicht: Kommentare bearbeiten, Kommentare unter dem eigenen Beitrag löschen, Likes, Suche in Beiträgen, Entwürfe, Bilder in Beiträgen (dann mit Upload- und Moderationskonzept).
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
| **R-3** | Qualität der Testfragen entscheidet über P2. | Fragen werden als eigener, abgegrenzter Task erstellt und gegen FR-T2 bis FR-T4 geprüft. v1 lieferte zu ausgeglichene Ergebnisse, deshalb v2 mit fünf Antworten je Frage (D-65). |
| **R-4** | Schwellenwert `T` (FR-T11) ist erst nach echten Durchläufen kalibrierbar. | Konfigurierbar halten, Standard 2. |
| **R-5** | Das Fünfeck ist die anspruchsvollste UI-Aufgabe, besonders mobil. | Zwei eigenständige Layouts (NFR-3), früh im Meilenstein einplanen. |
| **R-6** | Fremdprofile berühren personenbezogene Daten Dritter. | Nicht in v1. Anforderungen dazu in §8.1 festgehalten. |
| **R-7** | Ab v1.3 sehen Nutzende erstmals Eingaben anderer (Cross-Site-Scripting, Spam, Beleidigungen). | Markdown ohne HTML und ohne Bilder, Escaping überall, Längen- und Mengengrenzen je Person, Melden und Admin (D-80, D-81). Ausdrücklicher Injektionstest gegen Beiträge, Kommentare und Auszüge. |

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
- Fragebogen v1 mit 30 Fragen erfüllt die Paar-Balance aus FR-T3 nachweislich (per Test abgesichert).
- Auswertung folgt FR-T10 bis FR-T12; die Regel ist mit Beispielfällen getestet.
- Ergebnisübernahme funktioniert eingeloggt wie auch über den Zwischenspeicher nach Registrierung oder Login.
- Profil zeigt Farben und private Historie; Löschen eines Eintrags verhält sich nach FR-P8.

**v1.0**
- Fremde Profile sind nur eingeloggt sichtbar und zeigen keine Historie.
- Beide Suchen liefern korrekte Ergebnisse, insbesondere die Teilmengen-Logik aus FR-S3.
- Freundschaftsanfragen lassen sich senden, annehmen, ablehnen und auflösen.
- Über Freundeslisten ist der Graph navigierbar.

**v1.2**
- Eigenes und fremdes Profil sind dieselbe Seite; private Bereiche (Testhistorie, Einstellungen) sind für andere auf keinem Pfad erreichbar, ihre Adressen leiten auf das öffentliche Profil weiter.
- Die Pinnwand ist Standardtab und zeigt einen „Coming soon"-Platzhalter; private Adressen führen für andere Personen auf das Profil der Adresse weiter.
- Nickname, Bio und Farben lassen sich einzeln bearbeiten; das Speichern eines Bereichs verändert nie einen anderen, insbesondere nie die Testverknüpfung der Farben.
- Farben sind aus einem Testergebnis der Historie oder manuell am Fünfeck wählbar, mit und ohne JavaScript.
- Banner, Tabs und Sidebar funktionieren mit Tastatur und Screenreader und bei 375 px ohne horizontales Scrollen.
- Die Autorenkarte erscheint in Freundeslisten und Suchergebnissen.

**v1.2.1**
- Feedback lässt sich auf der Ergebnisseite ohne Seitenwechsel und über `/feedback/` (Footer-Link) abgeben, mit und ohne Login, mit und ohne JavaScript.
- Leere Absendungen, Bewertungen außerhalb 1 bis 5 und zu lange Texte werden abgelehnt; die Grenzen sind auch in der Datenbank festgehalten.
- Gespeichertes Feedback enthält nichts, was auf eine Person zeigt; die Datenschutzseite sagt das.
- Mehr als 5 Absendungen je IP-Adresse und Stunde werden abgelehnt, die Meldung ist auch bei HTMX sichtbar.

**v1.3**
- Beiträge lassen sich schreiben, bearbeiten, löschen und melden; mit und ohne Farbverknüpfung.
- Markdown erzeugt nie HTML aus Nutzereingaben: ein Injektionstest mit Skript-Tags, `javascript:`-Links, Bildsyntax und Roh-HTML besteht in Beitrag, Auszug und Vorschau.
- Der Tab „Posts" zeigt die Beiträge einer Person; die Color Infos zeigen bei gewählter Kombination genau deren Beiträge im Grid, mit Auszug statt Volltext.
- Für Gäste ist nirgends ein Beitrag sichtbar; jeder lesende Zugriff geht durch die zentrale Sichtbarkeitsprüfung.
- Account-Löschung entfernt Beiträge und Meldungen der Person, andere Beiträge bleiben.

**v1.4**
- Kommentare erhalten feste Nummern, die nach Löschen nicht neu vergeben werden (auch bei gleichzeitigem Schreiben eindeutig); Antworten verweisen mit „↪ #n".
- Ein gelöschter Kommentar mit Antworten bleibt als Hülle, ohne Text und Autor.
- Der Tab „Comments" zeigt die Kommentare einer Person; der Zähler neuer Kommentare zählt nur Fremdes und setzt sich beim Öffnen des Beitrags zurück.
- Account-Löschung macht fremde Kommentare zu Hüllen.

**v1.5**
- Beiträge und Kommentare lassen sich pinnen und lösen; die Pinnwand zeigt Autorenkarte und Link des Originals.
- Gelöschte Originale, Hüllen und für die ansehende Person unsichtbare Beiträge erscheinen nicht auf der Pinnwand.
- Mit ersatzweise leerer Sichtbarkeitsprüfung zeigt kein Pfad (Liste, Grid, Seite, Pinnwand) einen Beitrag: „nur Freunde" wäre eine Änderung an einer Stelle.
