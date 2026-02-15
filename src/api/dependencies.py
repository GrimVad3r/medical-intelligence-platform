"""FastAPI dependency injection."""

from typing import Generator

from sqlalchemy.orm import Session

from src.database.connection import get_session_factory


def get_db() -> Generator[Session, None, None]:
    factory = get_session_factory()
    session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
