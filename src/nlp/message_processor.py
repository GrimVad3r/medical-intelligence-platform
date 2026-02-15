"""Integrated NLP pipeline: NER -> classify -> link -> optional SHAP."""

from pathlib import Path
from typing import Any

from src.nlp.medical_ner import extract_entities
from src.nlp.text_classifier import classify
from src.nlp.entity_linker import link_entities
from src.logger import get_logger

logger = get_logger(__name__)


class MessageProcessor:
    def __init__(self, model_manager=None, base_dir: Path | None = None):
        self.model_manager = model_manager
        self.base_dir = base_dir or Path("data")

    def process(self, text: str, include_explanations: bool = False) -> dict[str, Any]:
        """Run full pipeline on text."""
        entities = extract_entities(text)
        classification = classify(text)
        linked = link_entities(entities, self.base_dir)
        out = {
            "entities": entities,
            "category": classification.get("category"),
            "confidence": classification.get("confidence"),
            "linked_entities": linked,
        }
        if include_explanations and self.model_manager:
            try:
                from src.nlp.shap_explainer import explain
                out["explanations"] = explain(text)
            except Exception as e:
                logger.warning("SHAP explanation skipped: %s", e)
        return out
