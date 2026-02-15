#!/usr/bin/env bash
# Cleanup build artifacts, caches, and optional DB/data for Medical Intelligence Platform.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

CLEAN_PYC=true
CLEAN_CACHE=true
CLEAN_LOGS=false
CLEAN_DIST=false
CLEAN_DBT=false
CLEAN_DATA=false
CLEAN_VENV=false

for arg in "$@"; do
  case "$arg" in
    --logs)     CLEAN_LOGS=true ;;
    --dist)     CLEAN_DIST=true ;;
    --dbt)      CLEAN_DBT=true ;;
    --data)     CLEAN_DATA=true ;;
    --venv)     CLEAN_VENV=true ;;
    --all)      CLEAN_LOGS=true; CLEAN_DIST=true; CLEAN_DBT=true; CLEAN_DATA=true ;;
  esac
done

rm -rf .pytest_cache .mypy_cache .coverage htmlcov
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true

[ "$CLEAN_LOGS" = true ] && rm -rf logs/*.log
[ "$CLEAN_DIST" = true ] && rm -rf dist build *.egg-info
[ "$CLEAN_DBT" = true ] && rm -rf dbt/target dbt/logs dbt/dbt_packages
[ "$CLEAN_DATA" = true ] && { echo "Data cleanup: remove data/*.json and nlp_models cache manually if desired"; }
[ "$CLEAN_VENV" = true ] && rm -rf .venv venv

echo "Cleanup completed."
