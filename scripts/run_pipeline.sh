#!/usr/bin/env bash
# Run a single pipeline stage: scrape -> NLP -> YOLO (optional) -> dbt.
# Usage: ./scripts/run_pipeline.sh [stage]
# Stages: scrape | nlp | yolo | dbt | all

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

# Load env if present
if [ -f .env ]; then
  set -a
  # shellcheck source=/dev/null
  source .env
  set +a
fi

STAGE="${1:-all}"
VENV_ACTIVATE="${VENV_PATH:-.venv}/bin/activate"
LOG_DIR="${LOG_DIR:-$PROJECT_ROOT/logs}"
mkdir -p "$LOG_DIR"

log() { echo "[$(date -Iseconds)] $*" | tee -a "$LOG_DIR/pipeline.log"; }
die() { log "ERROR: $*"; exit 1; }

[ -f "$VENV_ACTIVATE" ] || die "Virtualenv not found at $VENV_ACTIVATE"
# shellcheck source=/dev/null
source "$VENV_ACTIVATE"

run_scrape() {
  log "Running Telegram scrape..."
  python scripts/scrape_telegram.py --nlp --limit "${SCRAPE_LIMIT:-500}" || die "Scrape failed"
}

run_nlp() {
  log "Running NLP analysis (from DB)..."
  python scripts/analyze_nlp.py --from-db --limit "${NLP_LIMIT:-1000}" || die "NLP failed"
}

run_yolo() {
  log "Running YOLO analysis..."
  if [ -n "${YOLO_INPUT:-}" ] && [ -d "$YOLO_INPUT" ]; then
    python scripts/analyze_yolo.py "$YOLO_INPUT" --save-db ${YOLO_OUTPUT:+--output "$YOLO_OUTPUT"} || die "YOLO failed"
  else
    log "Skip YOLO: YOLO_INPUT not set or not a directory"
  fi
}

run_dbt() {
  log "Running dbt..."
  if [ -d dbt ] && command -v dbt &>/dev/null; then
    (cd dbt && dbt run --profiles-dir .) || die "dbt run failed"
  else
    log "Skip dbt: dbt project or CLI not found"
  fi
}

case "$STAGE" in
  scrape) run_scrape ;;
  nlp)    run_nlp ;;
  yolo)   run_yolo ;;
  dbt)    run_dbt ;;
  all)
    run_scrape
    run_nlp
    run_yolo
    run_dbt
    ;;
  *)
    echo "Usage: $0 {scrape|nlp|yolo|dbt|all}"
    exit 1
    ;;
esac

log "Pipeline stage '$STAGE' completed."
