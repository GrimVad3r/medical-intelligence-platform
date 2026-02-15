"""Dagster resources: DB, Telegram, NLP."""

from dagster import resource
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.config import get_settings


@resource
def db_resource():
    settings = get_settings()
    engine = create_engine(settings.database_url, pool_pre_ping=True)
    return sessionmaker(bind=engine, autocommit=False, autoflush=False)
