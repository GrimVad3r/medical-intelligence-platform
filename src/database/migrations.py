"""Database migrations – programmatic or Alembic hook."""

from sqlalchemy import Engine


def run_migrations(engine: Engine) -> None:
    """Run any programmatic migrations (e.g. alter table). Idempotent."""
    from sqlalchemy import text
    with engine.connect() as conn:
        # Example: Add new column if not exists
        try:
            conn.execute(text("ALTER TABLE messages ADD COLUMN IF NOT EXISTS processed BOOLEAN DEFAULT FALSE"))
        except Exception as e:
            # Ignore if already exists or not supported
            pass
        # Add more migrations as needed
