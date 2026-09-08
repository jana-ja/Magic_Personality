# Seed-Format für Farb-Content

Task 1.3 (D-28). Content liegt hier als versionierte JSON-Dateien statt
nur in der Datenbank — reproduzierbar, im Review sichtbar, in CI
testbar. Django Admin bleibt zusätzlich nutzbar, ist aber **nicht die
Quelle der Wahrheit**: Wer nur im Admin korrigiert, verliert die
Änderung beim nächsten `seed_content`-Lauf.

## Einspielen

```bash
python manage.py seed_content --locale en
```

Liest `seeds/colors_<locale>.json`. **Idempotent:** ein zweiter Lauf
mit unveränderter Datei ändert nichts an der Datenbank — bestehende
Zeilen werden abgeglichen (`update_or_create`), nie dupliziert.

Ein optionales `--path <datei>` liest stattdessen eine andere Datei
(vor allem für Tests).

## Dateiname und -struktur

Eine Datei je Sprache: `colors_en.json`, später z. B. `colors_de.json`.
Eine neue Sprache hinzuzufügen heißt: neue Datei anlegen und
`seed_content --locale de` laufen lassen — **keine neue Migration
nötig** (D-15). Das `locale`-Feld in der Datei muss zum `--locale`
der Kommandozeile passen, sonst bricht der Import ab.

```json
{
  "locale": "en",
  "combinations": [
    {
      "code": "W",
      "name": "White",
      "goal": "Peace",
      "means": "Order and structure",
      "guiding_question": "What is the right course of action?",
      "archetype": "",
      "traits": [
        {
          "name": "Compassion",
          "description": "Caring about the wellbeing of others.",
          "type": "STRENGTH",
          "leaning_toward": null
        },
        {
          "name": "Self-righteousness",
          "description": "Certainty that one's own rules are the correct ones.",
          "type": "WEAKNESS",
          "leaning_toward": "U"
        }
      ],
      "perspectives": []
    },
    {
      "code": "WB",
      "name": "Orzhov",
      "goal": "",
      "means": "",
      "guiding_question": "Who belongs, and who decides?",
      "archetype": "The Aristocrat",
      "theme": "Hierarchie",
      "traits": [],
      "perspectives": [
        {
          "from_color": "W",
          "poles": [
            { "color": "W", "term": "Ordnung" },
            { "color": "B", "term": "Willkür" }
          ],
          "text": "Sieht das Paar als moralische Ordnung."
        },
        { "from_color": "B", "text": "Sieht das Paar als nützliche Hierarchie." },
        { "from_color": null, "text": "Die Interessen der Gruppe gegen die des Einzelnen." }
      ]
    }
  ]
}
```

(Die Beispielwerte oben sind frei erfunden, nur zur Veranschaulichung
des Formats. Die echten Inhalte stehen seit Task 1.4 in
`colors_en.json` — siehe „Herkunft der Inhalte" am Ende.)

## Felder

### Oberste Ebene

| Feld | Pflicht | Beschreibung |
|---|---|---|
| `locale` | ja | Muss zum `--locale`-Argument passen. |
| `combinations` | ja | Liste von Kombinations-Einträgen, siehe unten. |

### Kombination

Ein Eintrag pro `ColorCombination`. Muss **nicht** für alle 31 Codes
vorhanden sein — nur seed, was schon Inhalt hat (Task 1.4 füllt das
schrittweise; nicht genannte Codes bleiben unverändert, so wie
Task 1.1s Datenmigration sie angelegt hat).

| Feld | Pflicht | Beschreibung |
|---|---|---|
| `code` | ja | Kanonisch WUBRG-sortiert, z. B. `"W"`, `"WU"`. Muss eine der 31 gültigen Kombinationen sein — jeder andere Wert bricht den Import mit einer klaren Fehlermeldung ab. |
| `name` | nein | Default `""`. |
| `goal` | nein | Default `""`. Nur bei Einzelfarben sinnvoll befüllt (PRD §5.2). |
| `means` | nein | Default `""`. Wie `goal`. |
| `guiding_question` | nein | Default `""`. |
| `archetype` | nein | Default `""`. Nur bei Zweierkombinationen sinnvoll befüllt. |
| `theme` | nein | Default `""`. Das eine Wort auf der Linie zwischen zwei Farben im Fünfeck: bei Ally das gemeinsame Anliegen (`"Design"`), bei Enemy das, was beide zusammen ergeben (`"Tribalism"`). Wie `archetype` nur bei Zweierkombinationen sinnvoll — nicht erzwungen. |
| `traits` | nein | Default `[]`. Nur bei Einzelfarben sinnvoll befüllt (FR-C-Tabelle in PRD §5.2). |
| `perspectives` | nein | Default `[]`. Nur bei **Enemy**-Zweierkombinationen zulässig — bei jeder anderen Kombinationsgröße oder einem Ally-Paar bricht der Import ab (PRD §6.1: "2-Farb-Enemy-Kombination"). |

### Eigenschaft (`traits[]`)

Ein Eintrag pro `Trait` samt seiner Verknüpfung zur Kombination
(`CombinationTrait`).

| Feld | Pflicht | Beschreibung |
|---|---|---|
| `name` | ja | Natürlicher Schlüssel zusammen mit `locale` — siehe Hinweis unten. |
| `description` | nein | Default `""`. |
| `type` | ja | `"STRENGTH"`, `"WEAKNESS"` oder `"NEUTRAL"`. Jeder andere Wert bricht ab. |
| `leaning_toward` | nein | `null` (center) oder ein Farbcode. Muss ein echter Rad-Nachbar der Kombinationsfarbe sein (Task 1.2) — nur bei Einzelfarben überhaupt zulässig. |

**Hinweis zum natürlichen Schlüssel:** `Trait` hat keine externe
ID/Slug wie andere Systeme das oft tun. `(name, locale)` ist der
Schlüssel, über den `seed_content` eine Eigenschaft wiedererkennt.
Das heißt: **den `name` einer bestehenden Eigenschaft zu ändern legt
eine neue Zeile an**, statt die alte umzubenennen — ein Rename ist
also bewusst nur über den Umweg "alten Eintrag entfernen, neuen
anlegen" möglich. Für den überschaubaren, kuratierten Bestand dieses
Projekts ist das eine bewusst einfache Lösung statt eines eigenen
Slug-Systems.

### Perspektive (`perspectives[]`)

| Feld | Pflicht | Beschreibung |
|---|---|---|
| `from_color` | nein | `null` (neutrale Sicht) oder eine der beiden Farben der Kombination. Jede andere Farbe bricht ab. |
| `text` | ja | Der ausführliche Text. Steht **nicht** am Fünfeck, sondern im Info-Bereich. |
| `poles` | nein | Default `[]`. Die kurzen Wörter am Fünfeck, siehe unten. |

### Pol (`perspectives[].poles[]`)

Ein Eintrag je Ende der Feind-Diagonale, also normalerweise genau zwei
je Perspektive — auch bei der **neutralen** Sicht (`from_color: null`).
Weiß sagt über das Paar W/B `"Good"` bei W und `"Evil"` bei B, Schwarz
sagt `"Codependency"` bei W und `"Individualism"` bei B, die neutrale
Sicht sagt `"Group"` und `"Individual"`.

| Feld | Pflicht | Beschreibung |
|---|---|---|
| `color` | ja | Eine der beiden Farben der Kombination. Jede andere bricht ab. Bestimmt, an welchem Ende der Diagonale das Wort steht. |
| `term` | ja | Ein Wort oder eine sehr kurze Wendung (`"Reason"`, `"Take it"`). |

## Validierung

`seed_content` lehnt ab (mit einer Fehlermeldung, die Ort und Ursache
nennt), statt fehlerhafte Daten still zu übernehmen:

- Unbekannte Felder auf jeder Ebene (Tippfehler wie `"guidin_question"`
  werden **nicht** stillschweigend ignoriert).
- Farbcodes, die nicht kanonisch WUBRG-sortiert oder ungültig sind.
- Eigenschafts-Typen und `leaning_toward`/`from_color`-Werte außerhalb
  der gültigen Farben.
- Alle Regeln aus den Modellen selbst (Tasks 1.1/1.2) — `leaning_toward`
  muss ein echter Rad-Nachbar sein, `Perspective` verlangt ein echtes
  Enemy-Paar, ein `poles[].color` muss zu den beiden Farben des Paares
  gehören, `combination` und `trait`/`locale` müssen zusammenpassen.

Ein fehlgeschlagener Import ändert **nichts** an der Datenbank — der
gesamte Lauf ist eine einzige Transaktion.

## Herkunft der Inhalte

`colors_en.json` ist mit Task 1.4 aus
<https://homosabiens.substack.com/p/the-mtg-color-wheel> (Duncan
Sabien) erfasst worden. Die Texte sind **paraphrasiert, nicht wörtlich
übernommen** (D-12); der Artikel wird in der Anwendung sichtbar als
Quelle genannt (PRD §9). Was aus welchem Abschnitt des Artikels kommt:

| Feld | Abschnitt der Quelle |
|---|---|
| `goal`, `means` (Einzelfarben) | Der Einleitungssatz je Farbe („White seeks …, through …"), auf ein Wort gekürzt — sie stehen an der Fünfeck-Ecke |
| `guiding_question` (Einzelfarben) | „A \<color\> agent, when presented with a decision or quandary, asks …" |
| `traits` (Einzelfarben) | Die Wortlisten („Other words associated with …") und die Absätze „From a negative perspective …" |
| `name`, `archetype`, `guiding_question` (Zweierkombinationen) | „Allies in Arms" und „Opposites in Harmony", inklusive der dort genannten Kürzel (Azorius, Orzhov …) |
| `traits` (Ally-Paare) | Das jeweils gemeinsame Anliegen der beiden verbündeten Farben |
| `perspectives[].text` (Feindpaare) | „Colors in Conflict" — die drei Sichten je Konflikt |
| `perspectives[].poles` | Dieselben drei Sichten, in ihre beiden Hälften zerlegt; die neutralen zusätzlich aus der Fünfeck-Grafik des Artikels |
| `theme` (Ally) | Das gemeinsame Anliegen aus „Allies in Arms“ (Design, Community, Progress, Independence, Authenticity) |
| `theme` (Enemy) | Das Ergebnis der Kombination aus „Opposites in Harmony“ (Tribalism, Heroism, Creativity, Truth seeking, Profanity) |
| `name` (3–5 Farben) | Die Dreifarb-Namen aus „Triple Major"; Vierfarb- und Fünffarb-Namen aus dem etablierten MTG-Sprachgebrauch (D-35) |

Nicht übernommen wurden die Beispielfiguren aus Pop-Kultur, die
Big-Five-Zuordnungen und die Anwendungsbeispiele des Artikels — sie
haben im Datenmodell (PRD §6.1) keinen Platz.

Eine inhaltliche Nebenbedingung, die das Format allein nicht erzwingt:
**`traits[].name` ist projektweit eindeutig** (D-36). Derselbe Name in
zwei Kombinationen ist über den natürlichen Schlüssel `(name, locale)`
(D-33) *eine* Zeile mit *einer* Beschreibung — die zweite Nennung
überschreibt die erste stillschweigend. Geteilte Eigenschaften sind
damit möglich, aber nur sinnvoll, wenn Beschreibung und Typ wirklich
für beide Kombinationen passen. `apps/colors/tests/test_seed_file_en.py`
prüft das mit.

Wie die Felder am Fünfeck landen, zeigen die Referenzzeichnungen in
`docs/reference/` — je eine für keine, eine und zwei selektierte Farben
(Ally und Enemy). `apps/colors/tests/test_seed_file_en.py` pinnt den
Default-Zustand (`default_0_selected.png`) Wort für Wort fest.
