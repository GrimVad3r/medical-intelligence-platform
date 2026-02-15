"""Database seeding from JSON and built-in data."""

from typing import Any, Callable

from sqlalchemy.orm import Session


def run_all_seeds(session_factory: Callable) -> None:
    """Run all built-in seed functions."""
    with session_factory() as session:
        _seed_medical_terms_placeholder(session)
        session.commit()


def _seed_medical_terms_placeholder(session: Session) -> None:
    """Optional: seed reference data. No-op if tables don't exist."""
    pass


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
