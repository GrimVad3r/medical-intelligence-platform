"""Logging setup for the application. Supports text/JSON format and optional file output."""

import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent


class JsonFormatter(logging.Formatter):
    """Structured JSON formatter for production log aggregation."""

    def format(self, record: logging.LogRecord) -> str:
        log = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            log["exception"] = self.formatException(record.exc_info)
        if getattr(record, "request_id", None):
            log["request_id"] = record.request_id
        return json.dumps(log)


def get_logger(name: str, level: str | None = None) -> logging.Logger:
    """Return a configured logger. Level and format from LOG_LEVEL, LOG_FORMAT, LOG_PATH."""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    log_level = (level or os.environ.get("LOG_LEVEL", "INFO")).upper()
    log_format = os.environ.get("LOG_FORMAT", "text").lower()
    log_path = os.environ.get("LOG_PATH")

    if log_format == "json":
        formatter: logging.Formatter = JsonFormatter()
    else:
        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        )

    handler: logging.Handler = logging.StreamHandler(sys.stderr)
    if log_path:
        Path(log_path).parent.mkdir(parents=True, exist_ok=True)
        handler = logging.FileHandler(log_path, encoding="utf-8")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(log_level)
    return logger
