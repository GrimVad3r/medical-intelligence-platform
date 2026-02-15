# Medical Intelligence Platform

NLP and YOLO-powered medical data analyzer that scrapes Telegram channels, analyzes content, stores results in a dbt-enabled PostgreSQL database, and exposes APIs, a Streamlit dashboard, and Dagster orchestration.

## Features

- **Telegram extraction**: Scrape and parse messages from configured channels with rate limiting
- **NLP pipeline**: Medical NER, text classification, entity linking, semantic analysis, SHAP explainability
- **YOLO image analysis**: Object detection on medical/device images with optional SHAP
- **Database**: PostgreSQL with SQLAlchemy, migrations, and dbt for transformations
- **API**: FastAPI with health, products, NLP, YOLO, explainability, and trends endpoints
- **Dashboard**: Multi-page Streamlit app (overview, products, pricing, images, NLP insights, explainability, Dagster monitoring)
- **Orchestration**: Dagster jobs, sensors, and schedules

## Quick start

```bash
# Clone and setup
git clone <repo-url> && cd medical-intelligence-platform
./scripts/setup.sh          # or scripts/setup.ps1 on Windows

# Configure
cp .env.example .env        # Set DATABASE_URL, TELEGRAM_API_ID, TELEGRAM_API_HASH, etc.

# Run pipeline
./scripts/run_pipeline.sh all

# Start services
uvicorn src.api.main:app --reload
streamlit run dashboards/streamlit_app.py
dagster dev -m src.orchestration.definitions
```

See [INSTALLATION.md](INSTALLATION.md) and [ARCHITECTURE.md](ARCHITECTURE.md) for details.

**Production:** Before deploy, run `python scripts/validate_env.py --load-env --production` and follow [DEPLOYMENT.md](DEPLOYMENT.md) and [docs/PRODUCTION_CHECKLIST.md](docs/PRODUCTION_CHECKLIST.md). Operations: [RUNBOOK.md](RUNBOOK.md).

## Project structure

| Area | Description |
|------|-------------|
| `src/` | Core code: NLP, extraction, database, transformation, YOLO, API, orchestration, utils |
| `dashboards/` | Streamlit app and pages |
| `scripts/` | CLI and automation (setup, scrape, analyze, pipeline, health, benchmark) |
| `tests/` | Unit, integration, and performance tests |
| `dbt/` | dbt models (staging, marts, intermediate) |
| `data/` | Knowledge bases, sample data, model cache |
| `docker/` | Dockerfile and docker-compose |
| `.github/` | CI/CD workflows |
| `k8s/` | Kubernetes manifests |

## License

See [LICENSE](LICENSE).
