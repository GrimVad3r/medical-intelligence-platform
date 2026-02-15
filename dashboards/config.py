"""Dashboard configuration."""

import os
from pathlib import Path

API_BASE = os.environ.get("API_BASE_URL", "http://localhost:8000")
DAGSTER_URL = os.environ.get("DAGSTER_URL", "http://localhost:3000")
