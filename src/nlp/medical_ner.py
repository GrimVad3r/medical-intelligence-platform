"""Medical named entity recognition."""

from typing import Any


def extract_entities(text: str, model=None) -> dict[str, list[dict[str, Any]]]:
    """Extract medical entities. Returns {label: [{text, start, end}, ...]}."""
    # Placeholder: integrate spaCy or transformers NER
    entities: dict[str, list[dict[str, Any]]] = {"DRUG": [], "CONDITION": [], "DOSAGE": []}
    if not text or not text.strip():
        return entities
    # Simple keyword fallback for demo
    words = text.split()
    for i, w in enumerate(words):
        if w.isdigit() and i > 0 and "mg" in words[min(i + 1, len(words) - 1)].lower():
            entities["DOSAGE"].append({"text": w, "start": 0, "end": len(w)})
    return entities
