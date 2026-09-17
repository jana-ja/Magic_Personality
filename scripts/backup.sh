#!/usr/bin/env bash
# Nächtliches Datenbank-Backup (Task 2.14, ARCHITECTURE.md §11.4).
#
# Läuft über einen Cron-Job auf dem Server (siehe docs/DEPLOYMENT.md,
# Abschnitt "Backups") — bewusst kein eigener vierter Container:
# ARCHITECTURE.md §2 sieht ausdrücklich nur drei vor (web, db, caddy).
# Der Dump entsteht *innerhalb* des laufenden "db"-Containers direkt
# in einem eigenen, benannten Docker-Volume ("postgres_backups",
# compose.prod.yaml) — "in ein Volume", nicht auf den Host-Dateisystem.
#
# Aufbewahrung 14 Tage: alte Dumps werden am Ende jedes Laufs entfernt,
# nicht separat per Cron — ein Lauf, eine Verantwortlichkeit.
set -euo pipefail

cd "$(dirname "$0")/.." # Verzeichnis mit compose.yaml/compose.prod.yaml

RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-14}"
TIMESTAMP="$(date -u +%Y-%m-%dT%H-%M-%SZ)"

COMPOSE=(docker compose -f compose.yaml -f compose.prod.yaml)

# PGPASSWORD statt POSTGRES_PASSWORD: pg_dump/psql lesen genau diesen
# Namen, der Container selbst kennt beide (siehe compose.yaml).
"${COMPOSE[@]}" exec -T db sh -c '
  set -euo pipefail
  mkdir -p /backups
  PGPASSWORD="$POSTGRES_PASSWORD" pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" \
    | gzip > "/backups/'"$TIMESTAMP"'.sql.gz"
  find /backups -name "*.sql.gz" -mtime "+'"$RETENTION_DAYS"'" -delete
'

echo "Backup geschrieben: ${TIMESTAMP}.sql.gz (Aufbewahrung ${RETENTION_DAYS} Tage)"
