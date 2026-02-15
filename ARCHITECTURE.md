# Architecture – Medical Intelligence Platform

## High-level flow

```
Telegram channels → Extraction (scraper + parser)
                         ↓
                   Raw messages / media
                         ↓
    ┌────────────────────┼────────────────────┐
    ↓                    ↓                    ↓
  NLP pipeline      YOLO (images)      Transformation
  (NER, classify,       ↓                    ↓
   link, SHAP)     Detections          Validators,
    ↓                    ↓              Cleaner, Agg
    └────────────────────┼────────────────────┘
                         ↓
              PostgreSQL (dbt models)
                         ↓
    ┌────────────────────┼────────────────────┐
    ↓                    ↓                    ↓
  FastAPI             Streamlit           Dagster
  (REST API)          (Dashboard)         (Orchestration)
```

## Components

### Extraction (`src/extraction/`)

- **telegram_scraper.py**: Telegram Client API usage, rate limiting, channel iteration
- **telegram_scraper_nlp.py**: Same plus inline NLP on each message
- **message_parser.py**: Normalize messages (text, media, entities)
- **rate_limiter.py**: Token-bucket or similar to respect Telegram limits

### NLP (`src/nlp/`)

- **medical_ner.py**: Entity recognition (drugs, conditions, etc.)
- **text_classifier.py**: Category/urgency classification
- **entity_linker.py**: Link entities to medical_terms.json / drug_database.json
- **message_processor.py**: Single entry point that runs NER → classify → link → optional SHAP
- **semantic_analyzer.py**: Relationships between entities
- **shap_explainer.py**: SHAP for text models
- **model_manager.py**: Load spacy/transformers models

### Database (`src/database/`)

- **connection.py**: Engine and session factory (from env)
- **models.py**: SQLAlchemy ORM (messages, products, nlp_results, yolo_results, etc.)
- **queries.py**: Common read/write helpers
- **migrations.py**: Programmatic migrations or Alembic hook
- **seeds.py**: Seed from JSON / built-in fixtures

### Transformation (`src/transformation/`)

- **validators.py**: Pydantic or custom validation
- **cleaner.py**: Normalize text, strip noise
- **aggregator.py**: Rollups for dashboard/API

### YOLO (`src/yolo/`)

- **model.py**: Load YOLO weights
- **inference.py**: Batch inference
- **postprocess.py**: NMS, thresholding
- **yolo_shap_explainer.py** / **explainability.py**: Image SHAP

### API (`src/api/`)

- **main.py**: FastAPI app, router includes
- **routes/**: products, nlp, yolo, explainability, health, trends
- **schemas.py**: Pydantic request/response models
- **dependencies.py**: DB session, config injection
- **middleware.py**: Error handling, logging

### Orchestration (`src/orchestration/`)

- **definitions.py**: Dagster assets and jobs
- **jobs.py**: Job definitions
- **sensors.py**: Schedules/sensors for scrape, NLP, dbt
- **resources.py**: DB, Telegram, NLP resources

### Dashboards (`dashboards/`)

- **streamlit_app.py**: Main app with page routing
- **pages/**: 01_overview, 02_products, 03_pricing, 04_images, 05_nlp_insights, 06_explainability, 07_dagster_monitoring, 08_settings
- **components/**: metrics, charts, nlp_viz, shap_viz, layout, styles

## Data flow (dbt)

- **staging**: Raw tables from application (messages, nlp_output, yolo_output)
- **intermediate**: Cleansed, joined
- **marts**: Analytics-ready (products, trends, KPIs)

## Security and configuration

- Secrets and URLs in environment (`.env`); never committed
- API keys for Telegram, optional external NLP APIs
- DB credentials via `DATABASE_URL`
