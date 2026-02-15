# Dagster Guide – Medical Intelligence Platform

## Role

Dagster orchestrates the full pipeline: trigger scrape → NLP → YOLO (if new images) → dbt run, on a schedule or via sensors.

## Definitions

- **definitions.py** – `Definitions(assets=[...], jobs=[...], sensors=[...], resources={...})`.
- **jobs.py** – Jobs such as `default_job` (full pipeline) or `scrape_job`, `nlp_job`, `dbt_job`.
- **sensors.py** – Schedule (e.g. daily) or sensor that reacts to new data.
- **resources.py** – Shared resources: DB connection, Telegram client, NLP model manager.

## Assets

Typical assets (implemented in `definitions.py`):

- `raw_messages` – Result of scrape (or read from DB).
- `nlp_results` – NLP output for new messages.
- `yolo_results` – YOLO output for new images.
- `dbt_models` – dbt run (via `dbt run` or dbt-dagster integration).

## Running

- **Dev UI:** `dagster dev -m src.orchestration.definitions`
- **CLI run:** `dagster job execute -m src.orchestration.definitions -j default_job`
- **Script:** `run_complete_pipeline.sh` can call Dagster after pipeline steps.

## Configuration

- Dagster config in `definitions.py` or YAML; secrets from env.
- Resources use same `DATABASE_URL`, Telegram credentials as the rest of the app.
