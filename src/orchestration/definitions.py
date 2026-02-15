"""Dagster definitions: assets, jobs, resources."""

from dagster import Definitions

from src.orchestration.jobs import default_job
from src.orchestration.resources import db_resource

defs = Definitions(
    jobs=[default_job],
    resources={"db": db_resource},
)
