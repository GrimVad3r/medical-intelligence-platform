# Troubleshooting – Medical Intelligence Platform

## Database

- **Connection refused** – Check PostgreSQL is running and `DATABASE_URL` in `.env`. Use `scripts/health_check.sh` to verify.
- **Extensions missing** – Run `python scripts/setup_db.py` (creates `pg_trgm`, `uuid-ossp`).
- **Migrations out of sync** – Run `python scripts/migrate_db.py` or `alembic upgrade head`.

## Telegram scraping

- **Flood wait** – Reduce `--limit` or increase delay in `rate_limiter.py`.
- **Auth required** – Set `TELEGRAM_API_ID`, `TELEGRAM_API_HASH`, and session (phone or `TELEGRAM_SESSION_STRING`).
- **Channel not found** – Use public username (e.g. `channelname`) or ensure bot/user has access.

## NLP

- **Out of memory** – Use smaller batch size, CPU, or smaller model in `src/nlp/config.py`.
- **Models not found** – Run with `--preload-models` or ensure `data/nlp_models/` is populated (see NLP_GUIDE.md).
- **Slow first request** – Models load on first use; use preload in production.

## YOLO

- **CUDA errors** – Install correct PyTorch/CUDA or set device to CPU in `src/yolo/config.py`.
- **No detections** – Lower confidence threshold via `--conf` or config.

## API / Dashboard

- **Port in use** – Change port: `uvicorn src.api.main:app --port 8001` or Streamlit `--server.port`.
- **CORS** – Configure in `src/api/main.py` if calling from another origin.

## Dagster

- **Module not found** – Run from project root: `dagster dev -m src.orchestration.definitions`.
- **Resource init fails** – Check env vars (e.g. `DATABASE_URL`) are set in the same shell as `dagster dev`.

## Logs

- Application logs: `logs/` (or as configured in `src/logger.py`).
- Pipeline: `logs/pipeline.log`, `logs/complete_pipeline.log`.
