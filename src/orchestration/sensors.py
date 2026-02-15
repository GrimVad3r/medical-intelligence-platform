"""Dagster sensors and schedules."""

from dagster import schedule, job


# @schedule(cron_schedule="0 2 * * *", job=default_job)  # daily 2am
# def daily_pipeline_schedule():
#     return {}
