#!/usr/bin/env python3
"""
Validate required environment variables before running the app or scripts.
Exit 0 if all required vars are set; non-zero and print missing to stderr otherwise.
"""

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Required for API + DB
REQUIRED_BASE = ["DATABASE_URL"]

# Required for Telegram scraping
REQUIRED_TELEGRAM = ["TELEGRAM_API_ID", "TELEGRAM_API_HASH"]

# Optional but recommended in production
RECOMMENDED_PRODUCTION = ["ENVIRONMENT", "CORS_ORIGINS"]


def validate(required: list[str], env: dict) -> list[str]:
    missing = []
    for key in required:
        val = env.get(key)
        if val is None or (isinstance(val, str) and not val.strip()):
            missing.append(key)
    return missing


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Validate environment for Medical Intelligence Platform")
    parser.add_argument("--telegram", action="store_true", help="Require Telegram vars")
    parser.add_argument("--production", action="store_true", help="Warn if recommended production vars missing")
    parser.add_argument("--load-env", action="store_true", help="Load .env file before validating")
    args = parser.parse_args()

    env = dict(os.environ)
    if args.load_env:
        env_file = PROJECT_ROOT / ".env"
        if env_file.exists():
            with open(env_file, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, _, v = line.partition("=")
                        env[k.strip()] = v.strip()

    required = list(REQUIRED_BASE)
    if args.telegram:
        required.extend(REQUIRED_TELEGRAM)

    missing = validate(required, env)
    if missing:
        print("Missing required environment variables:", ", ".join(missing), file=sys.stderr)
        sys.exit(1)

    if args.production:
        rec = validate(RECOMMENDED_PRODUCTION, env)
        if rec:
            print("Recommended for production:", ", ".join(rec), file=sys.stderr)

    print("Environment validation passed.")
    sys.exit(0)


if __name__ == "__main__":
    main()
