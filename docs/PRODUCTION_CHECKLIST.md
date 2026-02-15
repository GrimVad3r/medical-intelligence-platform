# Production readiness checklist

Use this to validate production-grade quality before release.

## Security

- [ ] No secrets in code or images; use env or secret manager.
- [ ] CORS restricted to known origins in production.
- [ ] API input validation (Pydantic) on all endpoints.
- [ ] Dependency scan (e.g. `safety`, `pip-audit`) in CI.
- [ ] Optional: API key or JWT for sensitive routes.
- [ ] HTTPS in front of API (ingress/TLS).

## Reliability

- [ ] Liveness probe (`/live`) does not depend on DB.
- [ ] Readiness probe (`/ready`) includes DB check.
- [ ] Graceful shutdown: FastAPI lifespan disposes DB pool.
- [ ] DB connection pool size and timeouts configured.
- [ ] Retries/timeouts for external calls (Telegram, etc.).
- [ ] Idempotent migrations and safe `setup_db`/migrate scripts.

## Observability

- [ ] Structured logging (JSON in production optional).
- [ ] Request ID or correlation ID in logs/middleware.
- [ ] Metrics endpoint or Prometheus integration (optional).
- [ ] Error tracking (e.g. Sentry) in production.
- [ ] RUNBOOK.md and DEPLOYMENT.md updated.

## Performance

- [ ] DB pool size and `pool_pre_ping` enabled.
- [ ] NLP/YOLO batch sizes and timeouts tuned.
- [ ] Resource limits (CPU/memory) set in K8s/Docker.
- [ ] Optional: caching for read-heavy endpoints.

## Operations

- [ ] Health check script (`scripts/health_check.sh`) used in probes.
- [ ] Env validation script (`scripts/validate_env.py`) before deploy.
- [ ] Backup/restore procedure documented and tested.
- [ ] CI: tests, lint, security scan, build (and optionally deploy).
