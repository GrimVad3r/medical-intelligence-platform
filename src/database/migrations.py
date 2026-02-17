"""Database migrations - programmatic fallback or Alembic hook."""

from sqlalchemy import Engine, inspect, text

from src.logger import get_logger

logger = get_logger(__name__)


def run_migrations(engine: Engine) -> None:
    """Run idempotent schema migrations and fail loudly on unexpected errors."""
    inspector = inspect(engine)
    with engine.begin() as conn:
        columns = {c["name"] for c in inspector.get_columns("messages")}
        if "processed" not in columns:
            conn.execute(
                text("ALTER TABLE messages ADD COLUMN processed BOOLEAN DEFAULT FALSE")
            )
            logger.info("Migration applied: messages.processed")
