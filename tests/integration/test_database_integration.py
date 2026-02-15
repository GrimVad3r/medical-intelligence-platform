"""Integration test: DB (requires DATABASE_URL)."""
import pytest
import os


@pytest.mark.skipif(
    "postgresql" not in os.environ.get("DATABASE_URL", "sqlite"),
    reason="Needs PostgreSQL",
)
def test_db_connection():
    from src.database.connection import get_engine
    from sqlalchemy import text
    engine = get_engine()
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
