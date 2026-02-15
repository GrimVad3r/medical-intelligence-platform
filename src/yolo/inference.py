"""YOLO inference pipeline."""

from pathlib import Path
from typing import Any

from src.yolo.model import YOLOModelManager
from src.yolo.postprocess import postprocess_results
from src.logger import get_logger

logger = get_logger(__name__)


def run_inference(
    model_manager: YOLOModelManager,
    image_paths: list[str],
    batch_size: int = 8,
    include_explanations: bool = False,
) -> dict[str, Any]:
    """Run detection on images. Returns {results: [{image_path, detections}, ...]}."""
    model = model_manager.load()
    if model is None:
        logger.warning("YOLO model not available; returning empty results")
        return {"results": [{"image_path": p, "detections": []} for p in image_paths]}

    conf = getattr(model_manager.config, "confidence_threshold", 0.5)
    results = []
    for path in image_paths:
        try:
            preds = model(str(path), conf=conf, verbose=False)
            detections = postprocess_results(preds)
            results.append({"image_path": path, "detections": detections})
        except Exception as e:
            logger.warning("Inference failed for %s: %s", path, e)
            results.append({"image_path": path, "detections": []})
    return {"results": results}
