# Deployment Guide – Medical Intelligence Platform

## Pre-deployment checklist

- [ ] All secrets in environment or secret manager (no `.env` in image).
- [ ] `DATABASE_URL` points to production DB; migrations run.
- [ ] `ENVIRONMENT=production` (or `staging`) set.
- [ ] CORS: `CORS_ORIGINS` set to allowed origins (not `*` in production).
- [ ] API rate limiting or WAF considered.
- [ ] Health probes: liveness (`/live`), readiness (`/ready`) configured in K8s/Docker.
- [ ] Resource limits (CPU/memory) set for API, workers, Dagster.
- [ ] Logging: structured/JSON in production; log level `INFO` or `WARNING`.
- [ ] Optional: Sentry (or similar) for error tracking; `SENTRY_DSN` set.
- [ ] Backup and restore tested for DB.
- [ ] Run `./scripts/validate_env.py` before first deploy.

## Docker production

```bash
docker build -t medical-intel-api:latest -f Dockerfile .
docker run --env-file .env.production -p 8000:8000 medical-intel-api:latest
```

Use `docker-compose.prod.yml` if provided; ensure healthcheck and restart policy.

## Kubernetes

1. Create namespace: `kubectl apply -f k8s/namespace.yml`
2. Create secrets from env or vault: `kubectl apply -f k8s/secrets.yml` (template only; fill values securely).
3. ConfigMap: `kubectl apply -f k8s/configmap.yml`
4. Deploy: `kubectl apply -f k8s/api-deployment.yml -f k8s/api-service.yml`
5. Verify: `kubectl get pods -n medical-intel` and hit `/ready`.

## Post-deployment

- Hit `/health` or `/ready` and confirm `database: "ok"`.
- Run a smoke test: `POST /nlp/analyze` with sample text.
- Confirm Dagster (if used) can connect to DB and run a job.
- Monitor logs and metrics for the first hour.
