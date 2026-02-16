"""Dagster job definitions."""

from pathlib import Path

from dagster import job, op


@op
def run_scrape_op():
    """Run Telegram scrape step."""
    import subprocess

    subprocess.run(
        ["python", "scripts/scrape_telegram.py", "--limit", "100"],
        check=True,
    )
    return "scrape_done"


@op
def run_nlp_op():
    """Run NLP on unprocessed messages."""
    import subprocess

    subprocess.run(
        ["python", "scripts/analyze_nlp.py", "--from-db", "--limit", "100"],
        check=True,
    )
    return "nlp_done"


@op
def run_dbt_op():
    """Run dbt."""
    import subprocess

    dbt_dir = Path("dbt")
    if not dbt_dir.exists():
        return "dbt_skipped"

    subprocess.run(
        ["dbt", "run", "--profiles-dir", "."],
        cwd=str(dbt_dir),
        check=True,
    )
    return "dbt_done"


@job
def default_job():
    run_dbt_op(run_nlp_op(run_scrape_op()))
