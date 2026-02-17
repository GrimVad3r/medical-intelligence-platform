"""Database connection and session management. Production: pool size and timeouts."""

from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.config import get_settings
from src.database.models import Base

_engine = None
_session_factory = None


def get_engine():
    global _engine
    if _engine is None:
        settings = get_settings()
        db_url = settings.database_url
        engine_kwargs = {"pool_pre_ping": True, "echo": False}
        if not db_url.startswith("sqlite"):
            engine_kwargs.update(
                {
                    "pool_size": getattr(settings, "database_pool_size", 5),
                    "max_overflow": getattr(settings, "database_max_overflow", 10),
                    "pool_timeout": getattr(settings, "database_pool_timeout", 30),
                }
            )
        _engine = create_engine(db_url, **engine_kwargs)
    return _engine


def dispose_engine() -> None:
    """Dispose engine and clear session factory. Call on app shutdown."""
    global _engine, _session_factory
    if _engine is not None:
        _engine.dispose()
        _engine = None
    _session_factory = None


def get_session_factory():
    global _session_factory
    if _session_factory is None:
        _session_factory = sessionmaker(bind=get_engine(), autocommit=False, autoflush=False)
    return _session_factory


@contextmanager
def get_session() -> Generator[Session, None, None]:
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
