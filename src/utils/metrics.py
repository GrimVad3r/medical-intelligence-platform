"""Performance metrics (counters, timers). Placeholder for Prometheus."""

from prometheus_client import Counter, Summary

_counters = {}
_timers = {}

def increment(name: str, value: float = 1, labels: dict[str, str] | None = None) -> None:
    label_names = tuple(sorted((labels or {}).keys()))
    key = (name, label_names)
    if key not in _counters:
        _counters[key] = Counter(name, f"Counter for {name}", list(label_names))
    if labels:
        _counters[key].labels(**labels).inc(value)
    else:
        _counters[key].inc(value)


def timing(name: str, value_seconds: float, labels: dict[str, str] | None = None) -> None:
    label_names = tuple(sorted((labels or {}).keys()))
    key = (name, label_names)
    if key not in _timers:
        _timers[key] = Summary(name, f"Timer for {name}", list(label_names))
    if labels:
        _timers[key].labels(**labels).observe(value_seconds)
    else:
        _timers[key].observe(value_seconds)
