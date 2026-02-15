# Changelog

## [0.1.0] - Unreleased

- Initial project structure
- NLP pipeline (NER, classifier, entity linker, SHAP placeholder)
- YOLO inference and postprocess
- Telegram scraper (Telethon)
- PostgreSQL + SQLAlchemy + dbt
- FastAPI (health, products, NLP, YOLO, explainability, trends)
- Streamlit dashboard (overview, products, pricing, images, NLP, explainability, Dagster, settings)
- Dagster job and resources
- Scripts: setup_db, seed_data, scrape_telegram, analyze_nlp, analyze_yolo, run_pipeline, health_check, benchmark, migrate_db, cleanup, setup
- Docker and docker-compose
- CI: tests and lint workflows
- K8s manifests and Prometheus config
