#!/usr/bin/env python3
"""
Database setup script for Medical Intelligence Platform.

Creates database, extensions, and initial schema. Safe to run multiple times
(idempotent). Requires PostgreSQL connection credentials from environment.
"""

import argparse
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from src.logger import get_logger
    from src.database.connection import get_engine, get_session_factory
    from src.database.migrations import run_migrations
    from src.database.models import Base
except ImportError as e:
    print(f"Import error: {e}. Ensure src is on PYTHONPATH.", file=sys.stderr)
    sys.exit(1)

logger = get_logger(__name__)


def create_extensions(engine):
    """Create required PostgreSQL extensions (e.g. pg_trgm, uuid-ossp)."""
    from sqlalchemy import text
    extensions = ["pg_trgm", "uuid-ossp"]
    with engine.connect() as conn:
        for ext in extensions:
            try:
                conn.execute(text(f'CREATE EXTENSION IF NOT EXISTS "{ext}"'))
                conn.commit()
                logger.info("Created extension: %s", ext)
            except Exception as e:
                logger.warning("Extension %s: %s", ext, e)
                conn.rollback()


def create_schema(engine):
    """Create all tables from SQLAlchemy models."""
    Base.metadata.create_all(bind=engine)
    logger.info("Schema (tables) created successfully.")


def run_dbt_init_if_present():
    """Run dbt debug/compile if dbt project exists."""
    dbt_dir = PROJECT_ROOT / "dbt"
    if not (dbt_dir / "dbt_project.yml").exists():
        logger.info("No dbt project found; skipping dbt init.")
        return
    import subprocess
    try:
        subprocess.run(
            ["dbt", "debug", "--project-dir", str(dbt_dir)],
            check=False,
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
        )
        logger.info("dbt debug completed.")
    except FileNotFoundError:
        logger.warning("dbt CLI not found; skip dbt steps or install dbt-core.")


def setup_database(
    create_tables: bool = True,
    run_migrations_flag: bool = True,
    extensions: bool = True,
    dbt_init: bool = False,
) -> bool:
    """
    Main setup routine: extensions, schema, migrations, optional dbt.

    Returns True on success, False on failure.
    """
    try:
        engine = get_engine()
        if extensions:
            create_extensions(engine)
        if create_tables:
            create_schema(engine)
        if run_migrations_flag:
            run_migrations(engine)
        if dbt_init:
            run_dbt_init_if_present()
        return True
    except Exception as e:
        logger.exception("Database setup failed: %s", e)
        return False


def main():
    parser = argparse.ArgumentParser(description="Setup Medical Intelligence Platform database.")
    parser.add_argument("--no-tables", action="store_true", help="Skip creating tables")
    parser.add_argument("--no-migrations", action="store_true", help="Skip running migrations")
    parser.add_argument("--no-extensions", action="store_true", help="Skip PostgreSQL extensions")
    parser.add_argument("--dbt-init", action="store_true", help="Run dbt debug after setup")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose logging")
    args = parser.parse_args()

    success = setup_database(
        create_tables=not args.no_tables,
        run_migrations_flag=not args.no_migrations,
        extensions=not args.no_extensions,
        dbt_init=args.dbt_init,
    )
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
