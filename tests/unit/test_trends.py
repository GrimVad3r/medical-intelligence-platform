from datetime import datetime, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.database.models import Base, NLPResult
from src.database.queries import get_trends_data


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    factory = sessionmaker(bind=engine)
    session = factory()
    now = datetime.utcnow()
    session.add(NLPResult(message_id=1, entities={}, linked_entities={}, created_at=now))
    session.add(
        NLPResult(
            message_id=2,
            entities={},
            linked_entities={},
            created_at=now - timedelta(days=1),
        )
    )
    session.commit()
    try:
        yield session
    finally:
        session.close()


def test_get_trends_data_day(db_session):
    series = get_trends_data(db_session, None, None, "day")
    assert len(series) >= 1
    assert {"date", "value"} <= set(series[0].keys())


def test_get_trends_data_invalid_granularity(db_session):
    with pytest.raises(ValueError):
        get_trends_data(db_session, None, None, "year")


def test_get_trends_data_invalid_range(db_session):
    with pytest.raises(ValueError):
        get_trends_data(db_session, "2026-02-10T00:00:00", "2026-02-01T00:00:00", "day")
