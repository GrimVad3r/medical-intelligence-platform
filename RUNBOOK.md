# Runbook – Medical Intelligence Platform

Operational procedures for production.

## Health checks

| Check | Command / Endpoint | Expected |
|-------|--------------------|----------|
| API liveness | `GET /live` or `curl -sf http://localhost:8000/live` | 200, `{"status":"ok"}` |
| API readiness | `GET /ready` or `GET /health` | 200, `database: "ok"` |
| Full stack | `./scripts/health_check.sh` | Exit 0 |
| Liveness only (K8s) | `./scripts/health_check.sh --live-only` | Exit 0 if API responds |

## Restarting services

```bash
# API (systemd example)
sudo systemctl restart medical-intel-api

# Docker Compose
docker compose restart api

# Kubernetes
kubectl rollout restart deployment/api -n medical-intel
```

## Database

- **Backup**: `./scripts/backup_db.sh` (writes to `backups/` or `BACKUP_DIR`)
- **Restore**: `./scripts/restore_db.sh backups/<file>.sql`
- **Migrations**: `python scripts/migrate_db.py` or `alembic upgrade head`
- **Connection issues**: Check `DATABASE_URL`, pool size, and PostgreSQL `max_connections`

## Logs

- Application: `logs/` or stdout (see `LOG_PATH`, `LOG_LEVEL`)
- Docker: `docker compose logs -f api`
- K8s: `kubectl logs -f deployment/api -n medical-intel`

## Common issues

| Symptom | Action |
|---------|--------|
| 502/503 on API | Check /live and /ready; restart pod/container; check DB connectivity |
| High latency | Check DB pool, NLP/YOLO model load; scale replicas or increase resources |
| Telegram scrape fails | Verify TELEGRAM_* env; check rate limits; see TROUBLESHOOTING.md |
| Out of memory | Increase container memory; reduce NLP batch size or YOLO batch |

## Escalation

1. Check RUNBOOK and TROUBLESHOOTING.md.
2. Review logs and metrics (Grafana/Prometheus if configured).
3. Contact maintainers (see SECURITY.md / CODE_OF_CONDUCT).
