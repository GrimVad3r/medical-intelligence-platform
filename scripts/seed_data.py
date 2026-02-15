#!/usr/bin/env python3
"""
Data seeding script for Medical Intelligence Platform.

Loads sample/fixture data from data/ and tests/fixtures/ into the database.
Uses src.database.seeds and optional JSON files.
"""

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from src.logger import get_logger
    from src.database.connection import get_session_factory
    from src.database import seeds
except ImportError as e:
    print(f"Import error: {e}. Ensure src is on PYTHONPATH.", file=sys.stderr)
    sys.exit(1)

logger = get_logger(__name__)

DATA_DIR = PROJECT_ROOT / "data"
FIXTURES_DIR = PROJECT_ROOT / "tests" / "fixtures"


def load_json_safe(path: Path) -> list | dict | None:
    """Load JSON file; return None on error."""
    if not path.exists():
        logger.warning("File not found: %s", path)
        return None
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        logger.error("Failed to load %s: %s", path, e)
        return None


def seed_from_file(session_factory, filepath: Path, dry_run: bool = False) -> int:
    """
    Seed database from a JSON file. Expects list of records or dict with 'records' key.
    Returns number of items processed (best-effort).
    """
    data = load_json_safe(filepath)
    if data is None:
        return 0
    records = data if isinstance(data, list) else data.get("records", data)
    if not isinstance(records, list):
        records = [data]
    if dry_run:
        logger.info("Dry run: would seed %d records from %s", len(records), filepath)
        return len(records)
    try:
        count = seeds.seed_from_records(session_factory, records, source=filepath.name)
        logger.info("Seeded %d records from %s", count, filepath.name)
        return count
    except Exception as e:
        logger.exception("Seeding failed for %s: %s", filepath, e)
        return 0


def run_builtin_seeds(session_factory, dry_run: bool = False) -> bool:
    """Run built-in seed functions from src.database.seeds."""
    if dry_run:
        logger.info("Dry run: skipping built-in seeds.")
        return True
    try:
        seeds.run_all_seeds(session_factory)
        logger.info("Built-in seeds completed.")
        return True
    except Exception as e:
        logger.exception("Built-in seeds failed: %s", e)
        return False


def main():
    parser = argparse.ArgumentParser(description="Seed Medical Intelligence Platform database.")
    parser.add_argument("--dry-run", action="store_true", help="Log actions without writing")
    parser.add_argument("--file", type=Path, help="Seed only from this JSON file")
    parser.add_argument("--data-dir", type=Path, default=DATA_DIR, help="Data directory")
    parser.add_argument("--fixtures-dir", type=Path, default=FIXTURES_DIR, help="Fixtures directory")
    args = parser.parse_args()

    session_factory = get_session_factory()
    total = 0

    if args.file:
        total += seed_from_file(session_factory, args.file.resolve(), args.dry_run)
    else:
        if not run_builtin_seeds(session_factory, args.dry_run):
            sys.exit(1)
        for name in ["sample_messages.json", "sample_data.json"]:
            for base in [args.data_dir, args.fixtures_dir]:
                path = base / name
                if path.exists():
                    total += seed_from_file(session_factory, path, args.dry_run)
                    break

    logger.info("Seeding finished. Total records processed: %d", total)
    sys.exit(0)


if __name__ == "__main__":
    main()
