"""Postprocess YOLO raw output to standard detections list."""

from typing import Any


def postprocess_results(predictions) -> list[dict[str, Any]]:
    """Convert ultralytics output to [{label, box: [x1,y1,x2,y2], confidence}, ...]."""
    out = []
    for pred in predictions:
        if hasattr(pred, "boxes"):
            for box in pred.boxes:
                xyxy = box.xyxy[0].tolist() if hasattr(box.xyxy, "__getitem__") else []
                cls_id = int(box.cls[0]) if hasattr(box, "cls") else 0
                conf = float(box.conf[0]) if hasattr(box, "conf") else 0.0
                name = pred.names.get(cls_id, "object") if hasattr(pred, "names") else "object"
                out.append({"label": name, "box": xyxy, "confidence": conf})
    return out
