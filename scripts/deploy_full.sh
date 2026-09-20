#!/usr/bin/env bash
# Vollständiges Deployment auf dem Server (D-77, docs/DEPLOYMENT.md,
# Abschnitt "Deploy-Skripte"): dieselben Schritte wie "Folge-
# Deployments" dort.
#
# Migrationen und Seeds laufen als eigene Schritte VOR "up -d" (D-29):
# sonst startet die neue Codeversion gegen ein noch altes Schema.
# "set -e" bricht beim ersten Fehler ab — schlägt migrate fehl, läuft
# der alte Stand unverändert weiter und "up -d" wird nie erreicht.
#
# Kommt eine neue Fragebogen-Version dazu (seeds/questionnaire_v<n>.json),
# hier eine seed_questionnaire-Zeile ergänzen.
set -euo pipefail

cd "$(dirname "$0")/.." # Verzeichnis mit compose.yaml/compose.prod.yaml

COMPOSE=(docker compose -f compose.yaml -f compose.prod.yaml)

"${COMPOSE[@]}" pull
"${COMPOSE[@]}" run --rm web python manage.py migrate
"${COMPOSE[@]}" run --rm web python manage.py seed_content --locale en
"${COMPOSE[@]}" run --rm web python manage.py seed_questionnaire --questionnaire-version 1 --locale en
"${COMPOSE[@]}" run --rm web python manage.py seed_questionnaire --questionnaire-version 2 --locale en
"${COMPOSE[@]}" up -d
"${COMPOSE[@]}" ps
