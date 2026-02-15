"""Link extracted entities to knowledge base (medical_terms, drug_database)."""

from pathlib import Path
from typing import Any

def load_kb(path: Path) -> dict:
    if not path.exists():
        return {}
    import json
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def link_entities(entities: dict[str, list], base_dir: Path | None = None) -> dict[str, Any]:
    """Map entity text to KB IDs. Returns {label: [{text, kb_id}, ...]}."""
    base_dir = base_dir or Path("data")
    linked = {}
    for label, items in (entities or {}).items():
        linked[label] = []
        for item in items:
            text = item.get("text", "") if isinstance(item, dict) else str(item)
            linked[label].append({"text": text, "kb_id": None})  # TODO: match against KB
    return linked
