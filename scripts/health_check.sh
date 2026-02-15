#!/usr/bin/env bash
# Health check for Medical Intelligence Platform: API, DB.
# Exit 0 if healthy, non-zero otherwise. Suitable for Docker/Kubernetes probes.
# --live-only: only check /live (no DB); use for K8s livenessProbe.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

LIVE_ONLY=false
for arg in "$@"; do
  case "$arg" in
    --live-only) LIVE_ONLY=true ;;
  esac
done

if [ -f .env ]; then
  set -a
  # shellcheck source=/dev/null
  source .env
  set +a
fi

API_URL="${API_URL:-http://localhost:8000}"
TIMEOUT="${HEALTH_TIMEOUT:-10}"
FAIL=0

# Liveness: /live (no DB). Readiness: /ready (with DB) or /health
if [ "$LIVE_ONLY" = true ]; then
  HEALTH_PATH="/live"
else
  HEALTH_PATH="${HEALTH_PATH:-/ready}"
fi

check_http() {
  if command -v curl &>/dev/null; then
    curl -sf --max-time "$TIMEOUT" "$API_URL$HEALTH_PATH" >/dev/null || return 1
  elif command -v wget &>/dev/null; then
    wget -qO- --timeout="$TIMEOUT" "$API_URL$HEALTH_PATH" >/dev/null || return 1
  else
    echo "Need curl or wget for HTTP check"
    return 1
  fi
}

check_db() {
  python -c "
import sys
sys.path.insert(0, '$PROJECT_ROOT')
try:
    from src.database.connection import get_engine
    from sqlalchemy import text
    e = get_engine()
    with e.connect() as c:
        c.execute(text('SELECT 1'))
    print('DB OK')
except Exception as err:
    print('DB FAIL:', err, file=sys.stderr)
    sys.exit(1)
" || return 1
}

echo "Health check: API=$API_URL path=$HEALTH_PATH live_only=$LIVE_ONLY"
if ! check_http; then
  echo "API health check failed"
  FAIL=1
fi
if [ "$LIVE_ONLY" = false ] && ! check_db; then
  echo "Database health check failed"
  FAIL=1
fi

exit $FAIL
