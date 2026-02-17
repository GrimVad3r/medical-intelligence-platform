"""FastAPI application entry point. Production: lifespan shutdown, CORS, security headers."""

from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from src.api.routes import health, nlp, products, trends, yolo, explainability
from src.api.security import require_api_key
from src.config import get_settings
from src.logger import get_logger

try:
    from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
except ImportError:  # pragma: no cover - optional in local dev
    CONTENT_TYPE_LATEST = "text/plain"

    def generate_latest() -> bytes:
        return b"prometheus client not installed"

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: optional Sentry
    settings = get_settings()
    if getattr(settings, "sentry_dsn", None):
        try:
            import sentry_sdk
            from sentry_sdk.integrations.fastapi import FastApiIntegration
            sentry_sdk.init(
                dsn=settings.sentry_dsn,
                environment=getattr(settings, "environment", "development"),
                integrations=[FastApiIntegration()],
            )
        except ImportError:
            pass
    yield
    # Shutdown: dispose DB pool for graceful exit
    try:
        from src.database.connection import dispose_engine
        dispose_engine()
        logger.info("Database engine disposed")
    except Exception as e:
        logger.warning("Shutdown dispose_engine: %s", e)


app = FastAPI(
    title="Medical Intelligence Platform API",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

settings = get_settings()
allow_credentials = all(origin != "*" for origin in settings.cors_origins)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)
from src.api.middleware import (
    LoggingMiddleware,
    RateLimitMiddleware,
    RequestIdMiddleware,
    SecurityHeadersMiddleware,
    parse_rate_limit,
)
# Order: last added runs first. RequestId first so Logging can use request_id.
app.add_middleware(LoggingMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestIdMiddleware)
if settings.api_rate_limit:
    limit, window_seconds = parse_rate_limit(settings.api_rate_limit)
    app.add_middleware(RateLimitMiddleware, limit=limit, window_seconds=window_seconds)

app.include_router(health.router, tags=["health"])
secured = [Depends(require_api_key)]
app.include_router(products.router, prefix="/v1/products", tags=["products"], dependencies=secured)
app.include_router(nlp.router, prefix="/v1/nlp", tags=["nlp"], dependencies=secured)
app.include_router(yolo.router, prefix="/v1/yolo", tags=["yolo"], dependencies=secured)
app.include_router(explainability.router, prefix="/v1/explainability", tags=["explainability"], dependencies=secured)
app.include_router(trends.router, prefix="/v1/trends", tags=["trends"], dependencies=secured)
# Backward compatibility: same routes without /v1
app.include_router(products.router, prefix="/products", tags=["products"], dependencies=secured)
app.include_router(nlp.router, prefix="/nlp", tags=["nlp"], dependencies=secured)
app.include_router(yolo.router, prefix="/yolo", tags=["yolo"], dependencies=secured)
app.include_router(explainability.router, prefix="/explainability", tags=["explainability"], dependencies=secured)
app.include_router(trends.router, prefix="/trends", tags=["trends"], dependencies=secured)


@app.get("/")
def root():
    return {"service": "medical-intelligence-platform", "version": "0.1.0", "docs": "/docs"}


@app.get("/live")
def live():
    """Liveness probe: no DB dependency. Use for K8s livenessProbe."""
    return {"status": "ok"}


@app.get("/metrics")
def metrics() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
