# Scripts – Medical Intelligence Platform

Scripts for setup, pipelines, health checks, and benchmarks. Run from project root with the virtualenv activated.

## Quick reference

| Script | Purpose |
|--------|--------|
| `validate_env.py` | **Production:** Validate required env vars before deploy |
| `setup.sh` | Initial setup: venv, deps, .env, DB, dbt |
| `setup_db.py` | Create DB extensions and schema; run migrations |
| `seed_data.py` | Seed DB from `data/` and `tests/fixtures/` |
| `scrape_telegram.py` | Scrape Telegram channels (optional NLP) |
| `analyze_nlp.py` | Run NLP on text, file, or unprocessed DB messages |
| `analyze_yolo.py` | Run YOLO on images; optional SHAP, save to DB |
| `run_pipeline.sh` | Run pipeline stage: scrape \| nlp \| yolo \| dbt \| all |
| `run_complete_pipeline.sh` | Full run: optional DB setup + pipeline + Dagster |
| `health_check.sh` | Check API and DB; use `--live-only` for K8s liveness |
| `backup_db.sh` | Backup PostgreSQL to `backups/` (or BACKUP_DIR) |
| `restore_db.sh` | Restore from backup file |
| `migrate_db.py` | Run SQL and/or Alembic migrations |
| `benchmark.py` | Benchmark NLP, YOLO, DB, API |
| `cleanup.sh` | Remove caches, logs, dist; optional --all |

## Examples

```bash
# From project root, with venv active
python scripts/setup_db.py
python scripts/seed_data.py --dry-run
python scripts/scrape_telegram.py "channel1,channel2" --limit 200 --nlp
python scripts/analyze_nlp.py --from-db --limit 500
python scripts/analyze_yolo.py data/sample_images --save-db --output results.json
./scripts/run_pipeline.sh all
./scripts/run_complete_pipeline.sh --setup-db
./scripts/health_check.sh
python scripts/benchmark.py --all --output logs/benchmark.json
python scripts/migrate_db.py --alembic upgrade head
./scripts/cleanup.sh --all
```

## Windows

Use Git Bash or WSL to run `.sh` scripts, or use the PowerShell equivalents in this folder (e.g. `run_pipeline.ps1`, `setup.ps1`).
