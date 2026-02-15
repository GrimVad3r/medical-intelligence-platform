#!/usr/bin/env bash
# Backup PostgreSQL database. Uses DATABASE_URL from env or .env.
# Output: backups/medical_intel_YYYYMMDD_HHMMSS.sql (or BACKUP_DIR env)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

if [ -f .env ]; then
  set -a
  # shellcheck source=/dev/null
  source .env
  set +a
fi

BACKUP_DIR="${BACKUP_DIR:-$PROJECT_ROOT/backups}"
mkdir -p "$BACKUP_DIR"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
FILE="$BACKUP_DIR/medical_intel_${TIMESTAMP}.sql"

# Parse DATABASE_URL: postgresql://user:pass@host:port/dbname
if [ -z "${DATABASE_URL:-}" ]; then
  echo "DATABASE_URL not set"
  exit 1
fi

# Use pg_dump if available and URL is postgresql
if [[ "$DATABASE_URL" == postgresql* ]] && command -v pg_dump &>/dev/null; then
  # Export PGPASSWORD and use pg_dump (strip schema from URL for pg_dump)
  export PGPASSWORD=$(echo "$DATABASE_URL" | sed -n 's/.*:\/\/[^:]*:\([^@]*\)@.*/\1/p')
  pg_dump -h "$(echo "$DATABASE_URL" | sed -n 's/.*@\([^:\/]*\).*/\1/p')" \
    -p "$(echo "$DATABASE_URL" | sed -n 's/.*:\([0-9]*\)\/.*/\1/p')" \
    -U "$(echo "$DATABASE_URL" | sed -n 's/.*:\/\/\([^:]*\):.*/\1/p')" \
    -d "$(echo "$DATABASE_URL" | sed -n 's/.*\/\([^?]*\).*/\1/p')" \
    -F p -f "$FILE" 2>/dev/null || true
  unset PGPASSWORD
  if [ -f "$FILE" ] && [ -s "$FILE" ]; then
    echo "Backup written to $FILE"
    exit 0
  fi
fi

echo "pg_dump not available or non-PostgreSQL URL. Use manual backup (e.g. pg_dump or cloud backup)."
echo "Placeholder backup dir: $BACKUP_DIR"
exit 1
