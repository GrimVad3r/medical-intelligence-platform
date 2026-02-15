#!/usr/bin/env python3
"""
Database migration runner for Medical Intelligence Platform.

Runs SQL migrations from sql/migrations/ and/or Alembic (if configured).
"""

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from src.logger import get_logger
    from src.database.connection import get_engine
    from src.database.migrations import run_migrations
except ImportError as e:
    print(f"Import error: {e}. Ensure src is on PYTHONPATH.", file=sys.stderr)
    sys.exit(1)

logger = get_logger(__name__)

SQL_MIGRATIONS_DIR = PROJECT_ROOT / "sql" / "migrations"


def run_sql_files(engine, directory: Path) -> int:
    """Execute .sql files in directory in lexicographic order. Returns count run."""
    from sqlalchemy import text
    if not directory.exists():
        logger.info("Migrations directory not found: %s", directory)
        return 0
    files = sorted(directory.glob("*.sql"))
    count = 0
    with engine.connect() as conn:
        for path in files:
            try:
                sql = path.read_text(encoding="utf-8")
                for stmt in sql.split(";"):
                    stmt = stmt.strip()
                    if stmt and not stmt.startswith("--"):
                        conn.execute(text(stmt))
                conn.commit()
                count += 1
                logger.info("Applied: %s", path.name)
            except Exception as e:
                logger.exception("Failed %s: %s", path.name, e)
                conn.rollback()
                raise
    return count


def run_alembic(args) -> bool:
    """Run Alembic if available."""
    try:
        import subprocess
        cmd = ["alembic"] + args
        result = subprocess.run(cmd, cwd=str(PROJECT_ROOT))
        return result.returncode == 0
    except FileNotFoundError:
        logger.warning("alembic not found; skip Alembic migrations")
        return True


def main():
    parser = argparse.ArgumentParser(description="Run database migrations.")
    parser.add_argument("--sql-dir", type=Path, default=SQL_MIGRATIONS_DIR, help="Directory of .sql files")
    parser.add_argument("--skip-sql", action="store_true", help="Do not run sql/migrations")
    parser.add_argument("--alembic", nargs="*", default=None, metavar="CMD", help="Run alembic with args (e.g. upgrade head)")
    args = parser.parse_args()

    engine = get_engine()
    if not args.skip_sql:
        run_sql_files(engine, args.sql_dir)
    if args.alembic is not None:
        if not run_alembic(args.alembic):
            sys.exit(1)
    else:
        run_migrations(engine)

    logger.info("Migrations completed.")
    sys.exit(0)


if __name__ == "__main__":
    main()
