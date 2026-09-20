#!/usr/bin/env bash
# Schnelles Deployment auf dem Server (D-77, docs/DEPLOYMENT.md,
# Abschnitt "Deploy-Skripte").
#
# Für einen neuen Stand ohne Schemaänderung und ohne neue Seed-Dateien:
# neues Image holen, Container erneuern, Zustand zeigen. Ändert der Stand
# etwas an der Datenbank (Migrationen) oder an den Seeds, stattdessen
# scripts/deploy_full.sh — hier läuft bewusst kein migrate (D-29).
set -euo pipefail

cd "$(dirname "$0")/.." # Verzeichnis mit compose.yaml/compose.prod.yaml

COMPOSE=(docker compose -f compose.yaml -f compose.prod.yaml)

"${COMPOSE[@]}" pull
"${COMPOSE[@]}" up -d
"${COMPOSE[@]}" ps
