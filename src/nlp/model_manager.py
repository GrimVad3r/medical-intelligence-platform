"""Load and cache NLP models (spacy, transformers)."""

from pathlib import Path
from typing import Any

from src.nlp.config import NLP_MODEL_PATH
from src.logger import get_logger

logger = get_logger(__name__)


class ModelManager:
    def __init__(self, model_path: Path | None = None):
        self.model_path = model_path or NLP_MODEL_PATH
        self._models: dict[str, Any] = {}

    def load_all(self) -> None:
        """Preload default models."""
        pass  # Load spacy/transformers into self._models

    def get_ner_model(self):
        return self._models.get("ner")

    def get_classifier_model(self):
        return self._models.get("classifier")
