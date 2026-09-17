# Seed-Format für den Fragebogen

Task 2.6 (D-16, D-28, FR-T6). Wie beim Farb-Content (siehe
`seeds/README.md`) liegt der Fragebogen als versionierte JSON-Datei im
Repository, nicht nur in der Datenbank.

## Einspielen

```bash
python manage.py seed_questionnaire --version 1 --locale en
```

Liest `seeds/questionnaire_v<version>.json`. **Idempotent**, solange
die Version noch nicht veröffentlicht ist: ein zweiter Lauf mit
unveränderter Datei ändert nichts, ein Lauf mit geänderten Fragen
aktualisiert sie (`update_or_create`).

Ein optionales `--path <datei>` liest stattdessen eine andere Datei
(vor allem für Tests).

## Veröffentlichung und Unveränderlichkeit (FR-T6)

Das Feld `"published"` (Default `false`) steuert, ob diese Version
freigegeben ist:

- **Solange `published` nie `true` war:** die Version ist ein Entwurf,
  Fragen und Antworten lassen sich beliebig ändern.
- **Sobald ein Lauf `"published": true` gesetzt hat:** `published_at`
  wird einmalig gesetzt. **Jeder weitere Lauf gegen dieselbe Version
  darf den Inhalt nicht mehr ändern** — abweichender Text, eine
  geänderte Dimension, eine neue oder fehlende Frage/Antwort brechen
  den Import mit einer klaren Fehlermeldung ab. Ein Lauf mit exakt
  unverändertem Inhalt bleibt möglich (idempotentes Redeploy).
  `"published": false` gegen eine bereits veröffentlichte Version
  bricht ebenfalls ab — zurückziehen ist nicht vorgesehen.

Um Fragen einer veröffentlichten Version zu ändern: neue
Versionsnummer vergeben (neue Datei `questionnaire_v2.json`), nicht
die alte Datei bearbeiten.

## Dateiname und -struktur

```json
{
  "version": 1,
  "locale": "en",
  "published": false,
  "questions": [
    {
      "position": 1,
      "dimension": "INNER",
      "text": "Etwas gerät ins Wanken, das dir wichtig ist. Was ist dein erster innerer Impuls?",
      "answers": [
        { "color": "W", "text": "Ich halte an dem fest, was ich für richtig halte." },
        { "color": "B", "text": "Ich nutze den Moment, um mir zu nehmen, was ich brauche." }
      ]
    }
  ]
}
```

(Beispielwerte oben frei erfunden. Die echten 20 Fragen kommen mit
Task 2.7.)

## Felder

### Oberste Ebene

| Feld | Pflicht | Beschreibung |
|---|---|---|
| `version` | ja | Muss zum `--version`-Argument passen. |
| `locale` | ja | Muss zum `--locale`-Argument passen. |
| `published` | nein | Default `false`. Siehe oben. |
| `questions` | ja | Liste von Fragen, siehe unten. |

### Frage (`questions[]`)

| Feld | Pflicht | Beschreibung |
|---|---|---|
| `position` | ja | Zusammen mit `locale` der natürliche Schlüssel je Fragebogen-Version. |
| `dimension` | ja | `"INNER"`, `"OUTER"`, `"FEELING"` oder `"VALUES"` (FR-T4). Jeder andere Wert bricht ab. |
| `text` | ja | Die Situationsbeschreibung. Nennt die Farbzuordnung nicht (FR-T2). |
| `answers` | ja | Genau zwei Einträge, siehe unten (FR-T1). |

### Antwort (`questions[].answers[]`)

| Feld | Pflicht | Beschreibung |
|---|---|---|
| `color` | ja | Die Farbe, die bei Auswahl einen Punkt bekommt (FR-T5). Je Frage muss `color` sich unterscheiden — das erzwingt der Unique-Constraint auf `AnswerOption`. |
| `text` | ja | Eine typische Reaktion dieser Farbe, ohne die Farbe zu benennen (FR-T2). |

`locale` wird für Fragen und Antworten automatisch aus dem
Datei-Feld `locale` übernommen, nicht einzeln je Eintrag wiederholt.

## Validierung

`seed_questionnaire` lehnt ab (mit einer Fehlermeldung, die Ort und
Ursache nennt), statt fehlerhafte Daten still zu übernehmen:

- Unbekannte Felder auf jeder Ebene.
- `dimension`- und `color`-Werte außerhalb der gültigen Auswahl.
- Jede inhaltliche Änderung an einer bereits veröffentlichten Version
  (siehe oben).

Ein fehlgeschlagener Import ändert **nichts** an der Datenbank — der
gesamte Lauf ist eine einzige Transaktion.

Die Paar-Balance aus FR-T3 (jedes der 10 Farbpaare genau zweimal, jede
Farbe in genau 8 Fragen) prüft dieses Format nicht — das ist Aufgabe
eines eigenen Tests gegen die echte Seed-Datei (Task 2.7).
