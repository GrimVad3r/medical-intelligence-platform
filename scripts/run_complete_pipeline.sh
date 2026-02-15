#!/usr/bin/env bash
# Full orchestration: DB setup (optional), pipeline run, then Dagster materialization.
# Usage: ./scripts/run_complete_pipeline.sh [--setup-db] [--skip-dagster]

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

SETUP_DB=false
SKIP_DAGSTER=false
for arg in "$@"; do
  case "$arg" in
    --setup-db)     SETUP_DB=true ;;
    --skip-dagster) SKIP_DAGSTER=true ;;
  esac
done

VENV_ACTIVATE="${VENV_PATH:-.venv}/bin/activate"
LOG_DIR="${LOG_DIR:-$PROJECT_ROOT/logs}"
mkdir -p "$LOG_DIR"

log() { echo "[$(date -Iseconds)] $*" | tee -a "$LOG_DIR/complete_pipeline.log"; }
die() { log "ERROR: $*"; exit 1; }

[ -f "$VENV_ACTIVATE" ] || die "Virtualenv not found at $VENV_ACTIVATE"
# shellcheck source=/dev/null
source "$VENV_ACTIVATE"

if [ "$SETUP_DB" = true ]; then
  log "Setting up database..."
  python scripts/setup_db.py || die "DB setup failed"
fi

log "Running full pipeline (scrape -> nlp -> yolo -> dbt)..."
bash scripts/run_pipeline.sh all || die "Pipeline failed"

if [ "$SKIP_DAGSTER" = false ]; then
  if command -v dagster &>/dev/null; then
    log "Triggering Dagster job (if defined)..."
    dagster job execute -m src.orchestration.definitions -j default_job 2>/dev/null || true
  else
    log "Dagster CLI not found; skip orchestration step."
  fi
fi

log "Complete pipeline finished successfully."
