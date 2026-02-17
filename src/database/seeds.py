"""Database seeding from JSON and built-in data."""

from typing import Any, Callable

from sqlalchemy.orm import Session


def run_all_seeds(session_factory: Callable) -> None:
    """Run all built-in seed functions."""
    with session_factory() as session:
        _seed_medical_terms_placeholder(session)
        session.commit()


def _seed_medical_terms_placeholder(session: Session) -> None:
    """Seed medical terms from data/medical_terms.json if table exists."""
    from sqlalchemy import inspect
    import json
    from pathlib import Path
    inspector = inspect(session.bind)
    if "medical_terms" in inspector.get_table_names():
        terms_path = Path("data/medical_terms.json")
        if terms_path.exists():
            with open(terms_path, "r", encoding="utf-8") as f:
                terms = json.load(f)
            for term in terms:
                session.execute(
                    "INSERT INTO medical_terms (name, description) VALUES (:name, :description)",
                    {"name": term.get("name", ""), "description": term.get("description", "")}
                )


def seed_from_records(session_factory: Callable, records: list[dict[str, Any]], source: str = "") -> int:
    """Insert records into appropriate tables. Returns count inserted."""
    from src.database.models import Message

    count = 0
    with session_factory() as session:
        for r in records:
            if "text" in r or "channel_id" in r:
                msg = Message(
                    channel_id=r.get("channel_id", "seed"),
                    external_id=r.get("external_id", str(count)),
                    text=r.get("text", ""),
                    raw=r,
                )
                session.add(msg)
                count += 1
        session.commit()
    return count
