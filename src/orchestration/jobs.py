"""Dagster job definitions."""

from dagster import job, op


@op
def run_scrape_op():
    """Run Telegram scrape step."""
    from scripts.scrape_telegram import main as scrape_main
    import sys
    sys.argv = ["scrape_telegram.py", "--limit", "100"]
    # In practice: use resources to get channel list and run scraper
    return "scrape_done"


@op
def run_nlp_op():
    """Run NLP on unprocessed messages."""
    return "nlp_done"


@op
def run_dbt_op():
    """Run dbt."""
    return "dbt_done"


@job
def default_job():
    run_dbt_op(run_nlp_op(run_scrape_op()))
