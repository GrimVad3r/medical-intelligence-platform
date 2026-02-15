"""Aggregation logic for analytics and dashboard."""

from collections import Counter
from typing import Any


def aggregate_entities(results: list[dict[str, Any]]) -> dict[str, int]:
    """Count entity labels across NLP results."""
    counts: Counter = Counter()
    for r in results:
        entities = r.get("entities") or {}
        if isinstance(entities, dict):
            for label, items in entities.items():
                if isinstance(items, list):
                    counts[label] += len(items)
                else:
                    counts[label] += 1
        elif isinstance(entities, list):
            for e in entities:
                if isinstance(e, dict) and "label" in e:
                    counts[e["label"]] += 1
    return dict(counts)
