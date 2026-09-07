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
      "traits": [],
      "perspectives": [
        { "from_color": "W", "text": "Sieht das Paar als moralische Ordnung." },
        { "from_color": "B", "text": "Sieht das Paar als nützliche Hierarchie." },
        { "from_color": null, "text": "Die Interessen der Gruppe gegen die des Einzelnen." }
      ]
    }
  ]
}
```

(Die Beispielwerte oben sind frei erfunden, nur zur Veranschaulichung
des Formats — die echten, aus der Quelle paraphrasierten Inhalte
kommen mit Task 1.4.)

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
| `text` | ja | |

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
  Enemy-Paar, `combination` und `trait`/`locale` müssen zusammenpassen.

Ein fehlgeschlagener Import ändert **nichts** an der Datenbank — der
gesamte Lauf ist eine einzige Transaktion.
