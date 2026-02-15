"""YOLO model loading and management."""

from pathlib import Path
from typing import Any


class YOLOModelManager:
    def __init__(self, config=None):
        self.config = config
        self._model: Any = None

    def load(self) -> Any:
        """Load YOLO model. Lazy init."""
        if self._model is not None:
            return self._model
        try:
            from ultralytics import YOLO
            path = getattr(self.config, "model_path", Path("data/yolo_models"))
            model_path = path / "best.pt" if path.is_dir() else path
            if not str(model_path).endswith(".pt"):
                self._model = YOLO("yolov8n.pt")  # default
            else:
                self._model = YOLO(str(model_path))
            return self._model
        except ImportError:
            return None
