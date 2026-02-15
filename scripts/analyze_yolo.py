#!/usr/bin/env python3
"""
YOLO image analysis script for Medical Intelligence Platform.

Runs object detection on images (file, directory, or from DB) and optionally
SHAP explainability. Results can be saved to DB or JSON.
"""

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from src.logger import get_logger
    from src.yolo.inference import run_inference
    from src.yolo.model import YOLOModelManager
    from src.yolo.config import get_yolo_config
except ImportError as e:
    print(f"Import error: {e}. Ensure src is on PYTHONPATH.", file=sys.stderr)
    sys.exit(1)

logger = get_logger(__name__)

SUPPORTED_EXT = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def collect_images(path: Path) -> list[Path]:
    """Collect image paths from file or directory."""
    if path.is_file():
        return [path] if path.suffix.lower() in SUPPORTED_EXT else []
    return [p for p in path.rglob("*") if p.is_file() and p.suffix.lower() in SUPPORTED_EXT]


def main():
    parser = argparse.ArgumentParser(
        description="Run YOLO image analysis for Medical Intelligence Platform."
    )
    parser.add_argument("input", type=Path, nargs="?", help="Image file or directory")
    parser.add_argument("--output", type=Path, default=None, help="Write results JSON here")
    parser.add_argument("--explain", action="store_true", help="Run SHAP explainability (slower)")
    parser.add_argument("--conf", type=float, default=None, help="Confidence threshold (override config)")
    parser.add_argument("--save-db", action="store_true", help="Persist results to database")
    parser.add_argument("--batch-size", type=int, default=8, help="Batch size for inference")
    args = parser.parse_args()

    if not args.input or not args.input.exists():
        logger.error("Input path required and must exist: %s", args.input)
        sys.exit(1)

    images = collect_images(args.input)
    if not images:
        logger.error("No supported images found under %s", args.input)
        sys.exit(1)

    logger.info("Found %d images", len(images))

    config = get_yolo_config()
    if args.conf is not None:
        config.confidence_threshold = args.conf

    try:
        model_manager = YOLOModelManager(config)
        results = run_inference(
            model_manager,
            image_paths=[str(p) for p in images],
            batch_size=args.batch_size,
            include_explanations=args.explain,
        )
    except Exception as e:
        logger.exception("YOLO inference failed: %s", e)
        sys.exit(1)

    if args.save_db:
        try:
            from src.database.connection import get_session_factory
            from src.database.queries import save_yolo_results
            session_factory = get_session_factory()
            with session_factory() as session:
                save_yolo_results(session, results)
            logger.info("Results saved to database")
        except Exception as e:
            logger.exception("Failed to save to DB: %s", e)
            sys.exit(1)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, default=str)
        logger.info("Results written to %s", args.output)

    logger.info("YOLO analysis complete. Processed %d images.", len(images))
    sys.exit(0)


if __name__ == "__main__":
    main()
