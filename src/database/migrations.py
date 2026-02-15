"""Database migrations – programmatic or Alembic hook."""

from sqlalchemy import Engine


def run_migrations(engine: Engine) -> None:
    """Run any programmatic migrations (e.g. alter table). Idempotent."""
    # Placeholder: add ALTER TABLE or data migrations as needed
    pass
