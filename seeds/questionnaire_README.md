# Seed-Format für den Fragebogen

Task 2.6 (D-16, D-28, FR-T6). Wie beim Farb-Content (siehe
`seeds/README.md`) liegt der Fragebogen als versionierte JSON-Datei im
Repository, nicht nur in der Datenbank.

## Einspielen

```bash
python manage.py seed_questionnaire --questionnaire-version 1 --locale en
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
  geänderte Dimension oder Antwortreihenfolge, geänderte `choice_points`,
  eine neue oder fehlende Frage/Antwort brechen
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
      "dimension": "ACTION",
      "text": "Etwas gerät ins Wanken, das dir wichtig ist. Was ist dein erster innerer Impuls?",
      "answers": [
        { "color": "W", "text": "Ich halte an dem fest, was ich für richtig halte." },
        { "color": "B", "text": "Ich nutze den Moment, um mir zu nehmen, was ich brauche." }
      ]
    }
  ]
}
```

(Beispielwerte oben frei erfunden, im Format von v1. Die echten Fragen
stehen in `seeds/questionnaire_v1.json` (Task 2.7: 30 Fragen, je zwei
Antworten) und `seeds/questionnaire_v2.json` (Task 2.16, D-65: 15 Fragen,
je fünf Antworten, `"choice_points": [2, 1]`, `"result_threshold": 4`).)

## Felder

### Oberste Ebene

| Feld | Pflicht | Beschreibung |
|---|---|---|
| `version` | ja | Muss zum `--version`-Argument passen. |
| `locale` | ja | Muss zum `--locale`-Argument passen. |
| `published` | nein | Default `false`. Siehe oben. |
| `choice_points` | nein | Punkte je Rang, absteigend, z. B. `[2, 1]` = beste und zweitbeste Antwort wählen (D-65). Default `[1]` (eine Antwort, 1 Punkt, wie v1). Gehört zum Inhalt: bei einer veröffentlichten Version nicht mehr änderbar. |
| `result_threshold` | nein | `T` der Auswertungsregel (FR-T11) für diese Version. Default `2`. **Auch nach Veröffentlichung änderbar** (R-4), ein erneuter Lauf übernimmt den neuen Wert. |
| `questions` | ja | Liste von Fragen, siehe unten. |

### Frage (`questions[]`)

| Feld | Pflicht | Beschreibung |
|---|---|---|
| `position` | ja | Zusammen mit `locale` der natürliche Schlüssel je Fragebogen-Version. |
| `dimension` | ja | `"ACTION"`, `"MOTIVATION"` oder `"PERCEPTION"` (FR-T4, D-60). Jeder andere Wert bricht ab. |
| `text` | ja | Die Situationsbeschreibung. Nennt die Farbzuordnung nicht (FR-T2). |
| `answers` | ja | Mehr Einträge als `choice_points` Ränge hat (v1: zwei, v2: fünf), siehe unten (FR-T1). Die Reihenfolge in der Datei ist die Anzeigereihenfolge und gehört zum Inhalt. |

### Antwort (`questions[].answers[]`)

| Feld | Pflicht | Beschreibung |
|---|---|---|
| `color` | ja | Die Farbe, die bei Auswahl die Punkte des gewählten Rangs bekommt (FR-T5). Je Frage muss `color` sich unterscheiden — das erzwingt der Unique-Constraint auf `AnswerOption`. |
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

Aufbau und Balance einer konkreten Version (v1: Paar-Balance, D-60;
v2: jede Farbe an jeder Position, D-65) prüft dieses Format nicht — das
übernehmen `apps/quiz/tests/test_questionnaire_v1.py` und
`apps/quiz/tests/test_questionnaire_v2.py` gegen die echten Seed-Dateien.
