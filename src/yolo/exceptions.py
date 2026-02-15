"""YOLO-specific exceptions."""


class YOLOError(Exception):
    """Base for YOLO errors."""


class ModelLoadError(YOLOError):
    """Failed to load YOLO model."""
