"""Health check endpoints: /health (full), /ready (strict readiness with DB), /live (liveness only)."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from src.api.dependencies import get_db
from src.api.schemas import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health(db: Session = Depends(get_db)):
    """Full health: includes DB check. Use for monitoring."""
    db_status = "ok"
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        db_status = "error"
    return HealthResponse(status="ok", database=db_status)


@router.get("/ready", response_model=HealthResponse)
def ready(db: Session = Depends(get_db)):
    """Readiness probe: DB must be up. Use for K8s readinessProbe."""
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        raise HTTPException(status_code=503, detail="database unavailable") from e
    return HealthResponse(status="ok", database="ok")
