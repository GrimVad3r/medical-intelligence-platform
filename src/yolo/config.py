"""YOLO configuration."""

import os
from pathlib import Path


def get_yolo_config():
    class Config:
        model_path = Path(os.environ.get("YOLO_MODEL_PATH", "data/yolo_models"))
        confidence_threshold = float(os.environ.get("YOLO_CONFIDENCE", "0.5"))
        device = os.environ.get("YOLO_DEVICE", "cpu")
    return Config()
