"""Performance metrics (counters, timers). Placeholder for Prometheus."""

from typing import Any


def increment(name: str, value: float = 1, labels: dict[str, str] | None = None) -> None:
    pass  # Hook to Prometheus or statsd


def timing(name: str, value_seconds: float, labels: dict[str, str] | None = None) -> None:
    pass
