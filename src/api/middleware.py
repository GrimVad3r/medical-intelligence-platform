"""Custom middleware: security headers, request ID, error handling, logging."""

from collections import defaultdict, deque
import time
import uuid
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from src.logger import get_logger

logger = get_logger(__name__)

REQUEST_ID_HEADER = "X-Request-ID"
REQUEST_ID_STATE = "request_id"


def parse_rate_limit(rate_limit: str) -> tuple[int, int]:
    """Parse rate limit format '<count>/<unit>' where unit is second|minute|hour."""
    count_raw, unit_raw = rate_limit.split("/", 1)
    count = int(count_raw.strip())
    unit = unit_raw.strip().lower()
    if unit in {"s", "sec", "second", "seconds"}:
        window = 1
    elif unit in {"m", "min", "minute", "minutes"}:
        window = 60
    elif unit in {"h", "hr", "hour", "hours"}:
        window = 3600
    else:
        raise ValueError(f"Unsupported rate limit unit: {unit_raw}")
    if count <= 0:
        raise ValueError("Rate limit count must be positive")
    return count, window


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security-related response headers."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        return response


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Generate or propagate request ID; add to response and request state for logging."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = request.headers.get(REQUEST_ID_HEADER) or str(uuid.uuid4())
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers[REQUEST_ID_HEADER] = request_id
        return response


class LoggingMiddleware(BaseHTTPMiddleware):
    """Log request method, path, status, duration and optional request_id."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start = time.perf_counter()
        response = await call_next(request)
        duration = time.perf_counter() - start
        request_id = getattr(request.state, "request_id", None)
        extra = {"request_id": request_id} if request_id else {}
        logger.info(
            "%s %s %d %.3fs",
            request.method,
            request.url.path,
            response.status_code,
            duration,
            extra=extra,
        )
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple in-memory fixed-window rate limiter by client IP."""

    def __init__(self, app, limit: int, window_seconds: int):
        super().__init__(app)
        self.limit = limit
        self.window_seconds = window_seconds
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        client = request.client.host if request.client else "unknown"
        now = time.time()
        hit_window = self._hits[client]
        while hit_window and now - hit_window[0] > self.window_seconds:
            hit_window.popleft()
        if len(hit_window) >= self.limit:
            return Response(status_code=429, content="rate limit exceeded")
        hit_window.append(now)
        return await call_next(request)
