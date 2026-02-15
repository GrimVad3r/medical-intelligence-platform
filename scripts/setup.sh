#!/usr/bin/env bash
# Initial setup for Medical Intelligence Platform: venv, deps, env, DB, dbt.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

PYTHON="${PYTHON:-python3}"
VENV_DIR="${VENV_PATH:-.venv}"

echo "Setup: Medical Intelligence Platform"
echo "Project root: $PROJECT_ROOT"

if [ ! -d "$VENV_DIR" ]; then
  echo "Creating virtualenv at $VENV_DIR..."
  "$PYTHON" -m venv "$VENV_DIR"
fi
# shellcheck source=/dev/null
source "$VENV_DIR/bin/activate"

echo "Upgrading pip and installing dependencies..."
pip install -U pip
pip install -r requirements.txt
[ -f requirements-dev.txt ] && pip install -r requirements-dev.txt
[ -f requirements-nlp.txt ] && pip install -r requirements-nlp.txt

if [ ! -f .env ] && [ -f .env.example ]; then
  echo "Copying .env.example to .env..."
  cp .env.example .env
  echo "Edit .env with your API keys and database URL."
fi

echo "Installing package in editable mode..."
pip install -e .

echo "Setting up database..."
python scripts/setup_db.py || { echo "DB setup failed (check DATABASE_URL in .env)"; exit 1; }

if [ -d dbt ] && command -v dbt &>/dev/null; then
  echo "Initializing dbt..."
  (cd dbt && dbt deps --profiles-dir . 2>/dev/null || true)
fi

echo "Setup complete. Activate with: source $VENV_DIR/bin/activate"
