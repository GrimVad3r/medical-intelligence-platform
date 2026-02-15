#!/usr/bin/env bash
# Restore PostgreSQL from a backup file. Uses DATABASE_URL from env.
# Usage: ./scripts/restore_db.sh backups/medical_intel_YYYYMMDD_HHMMSS.sql

set -euo pipefail

if [ $# -lt 1 ]; then
  echo "Usage: $0 <backup.sql>"
  exit 1
fi

BACKUP_FILE="$1"
if [ ! -f "$BACKUP_FILE" ]; then
  echo "File not found: $BACKUP_FILE"
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

if [ -f .env ]; then
  set -a
  # shellcheck source=/dev/null
  source .env
  set +a
fi

if [ -z "${DATABASE_URL:-}" ]; then
  echo "DATABASE_URL not set"
  exit 1
fi

if [[ "$DATABASE_URL" != postgresql* ]] || ! command -v psql &>/dev/null; then
  echo "Restore requires PostgreSQL and psql. Run manually: psql <connection> -f $BACKUP_FILE"
  exit 1
fi

echo "WARNING: This will overwrite the database. Ctrl+C to abort, Enter to continue."
read -r

export PGPASSWORD=$(echo "$DATABASE_URL" | sed -n 's/.*:\/\/[^:]*:\([^@]*\)@.*/\1/p')
psql -h "$(echo "$DATABASE_URL" | sed -n 's/.*@\([^:\/]*\).*/\1/p')" \
  -p "$(echo "$DATABASE_URL" | sed -n 's/.*:\([0-9]*\)\/.*/\1/p')" \
  -U "$(echo "$DATABASE_URL" | sed -n 's/.*:\/\/\([^:]*\):.*/\1/p')" \
  -d "$(echo "$DATABASE_URL" | sed -n 's/.*\/\([^?]*\).*/\1/p')" \
  -f "$BACKUP_FILE"
unset PGPASSWORD
echo "Restore completed from $BACKUP_FILE"
