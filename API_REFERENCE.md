# API Reference – Medical Intelligence Platform

Base URL (local): `http://localhost:8000`. Versioned routes: `/v1/...` (preferred for new clients).

## Health

- **GET /live** – Liveness only (no DB). Use for K8s `livenessProbe`. Returns `{"status": "ok"}`.
- **GET /ready** – Readiness (includes DB check). Use for K8s `readinessProbe`.
- **GET /health** – Full health; returns `{"status": "ok", "database": "ok"|"error"}`.

## Products

- **GET /products** – List products (from DB/dbt marts). Query: `limit`, `offset`, `category`.
- **GET /products/{id}** – Product detail.

## NLP

- **POST /nlp/analyze** – Body: `{"text": "..."}`. Returns NER, classification, entities.
- **GET /nlp/insights** – Aggregated NLP insights (entity counts, top categories). Query: `since`, `limit`.

## YOLO

- **POST /yolo/analyze** – Upload image or send URL. Returns detections (boxes, labels, scores).
- **GET /yolo/results** – List recent YOLO runs. Query: `limit`, `image_id`.

## Explainability (SHAP)

- **POST /explainability/nlp** – Body: `{"text": "..."}`. Returns SHAP values for NLP model.
- **POST /explainability/yolo** – Image + optional bbox. Returns SHAP for detection.

## Trends / Analytics

- **GET /trends** – Time-series or aggregated metrics. Query: `from`, `to`, `granularity`.

## Authentication

Currently no auth; add API key or JWT in middleware as needed (see `src/api/middleware.py`).

## OpenAPI

- **GET /docs** – Swagger UI.
- **GET /redoc** – ReDoc.
- **GET /openapi.json** – OpenAPI schema.
