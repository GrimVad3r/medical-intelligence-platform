#!/usr/bin/env python3
"""
Performance benchmark script for Medical Intelligence Platform.

Measures throughput and latency for NLP, YOLO, API, and database operations.
Outputs results to stdout and optional JSON file.
"""

import argparse
import json
import sys
import time
from pathlib import Path
from statistics import mean, stdev

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from src.logger import get_logger
except ImportError:
    import logging
    def get_logger(n):
        return logging.getLogger(n)

logger = get_logger(__name__)


def _run_trials(fn, n_trials: int = 5) -> tuple[list[float], float, float]:
    """Run fn() n_trials times; return (times, mean, stdev)."""
    times = []
    for _ in range(n_trials):
        start = time.perf_counter()
        fn()
        times.append(time.perf_counter() - start)
    return times, mean(times), (stdev(times) if len(times) > 1 else 0.0)


def benchmark_nlp(sample_text: str, n_trials: int) -> dict:
    """Benchmark NLP pipeline on sample text."""
    try:
        from src.nlp.message_processor import MessageProcessor
        from src.nlp.model_manager import ModelManager
    except ImportError:
        return {"error": "NLP module not available", "mean_s": 0}

    manager = ModelManager()
    manager.load_all()
    processor = MessageProcessor(model_manager=manager)

    def run():
        processor.process(sample_text, include_explanations=False)

    times, mu, sigma = _run_trials(run, n_trials)
    return {
        "mean_s": round(mu, 4),
        "stdev_s": round(sigma, 4),
        "times_s": [round(t, 4) for t in times],
        "throughput_1s": round(1 / mu, 2) if mu > 0 else 0,
    }


def benchmark_yolo(image_paths: list[str], n_trials: int, batch_size: int) -> dict:
    """Benchmark YOLO inference."""
    try:
        from src.yolo.inference import run_inference
        from src.yolo.model import YOLOModelManager
        from src.yolo.config import get_yolo_config
    except ImportError:
        return {"error": "YOLO module not available", "mean_s": 0}

    config = get_yolo_config()
    manager = YOLOModelManager(config)
    paths = image_paths[: min(16, len(image_paths))] or image_paths

    def run():
        run_inference(manager, image_paths=paths, batch_size=batch_size, include_explanations=False)

    times, mu, sigma = _run_trials(run, n_trials)
    n = len(paths)
    return {
        "mean_s": round(mu, 4),
        "stdev_s": round(sigma, 4),
        "images": n,
        "throughput_per_s": round(n / mu, 2) if mu > 0 else 0,
    }


def benchmark_db(n_ops: int, n_trials: int) -> dict:
    """Benchmark simple DB read/write."""
    try:
        from src.database.connection import get_session_factory
        from src.database.queries import get_unprocessed_messages
    except ImportError:
        return {"error": "Database module not available", "mean_s": 0}

    factory = get_session_factory()

    def run():
        with factory() as session:
            get_unprocessed_messages(session, limit=n_ops)

    times, mu, sigma = _run_trials(run, n_trials)
    return {
        "mean_s": round(mu, 4),
        "stdev_s": round(sigma, 4),
        "ops": n_ops,
        "throughput_ops_per_s": round(n_ops / mu, 2) if mu > 0 else 0,
    }


def benchmark_api(base_url: str, n_trials: int) -> dict:
    """Benchmark API health endpoint."""
    try:
        import urllib.request
    except ImportError:
        return {"error": "urllib not available", "mean_s": 0}

    url = f"{base_url.rstrip('/')}/health"

    def run():
        with urllib.request.urlopen(url, timeout=5) as _:
            pass

    times, mu, sigma = _run_trials(run, n_trials)
    return {
        "mean_s": round(mu, 4),
        "stdev_s": round(sigma, 4),
        "throughput_per_s": round(1 / mu, 2) if mu > 0 else 0,
    }


def main():
    parser = argparse.ArgumentParser(description="Benchmark Medical Intelligence Platform components.")
    parser.add_argument("--nlp", action="store_true", help="Benchmark NLP")
    parser.add_argument("--yolo", action="store_true", help="Benchmark YOLO (requires --yolo-images)")
    parser.add_argument("--yolo-images", type=Path, default=None, help="Directory of images for YOLO")
    parser.add_argument("--db", action="store_true", help="Benchmark DB queries")
    parser.add_argument("--api", action="store_true", help="Benchmark API health")
    parser.add_argument("--all", action="store_true", help="Run all benchmarks")
    parser.add_argument("--trials", type=int, default=5, help="Number of trials per benchmark")
    parser.add_argument("--output", type=Path, default=None, help="Write JSON results here")
    args = parser.parse_args()

    if not (args.nlp or args.yolo or args.db or args.api or args.all):
        parser.error("Specify at least one of: --nlp, --yolo, --db, --api, --all")

    results = {}
    sample_text = "Patient presented with hypertension and prescribed Lisinopril 10mg."

    if args.nlp or args.all:
        logger.info("Benchmarking NLP...")
        results["nlp"] = benchmark_nlp(sample_text, args.trials)
    if args.yolo or args.all:
        paths = []
        if args.yolo_images and args.yolo_images.exists():
            paths = [str(p) for p in args.yolo_images.iterdir() if p.suffix.lower() in {".jpg", ".png"}]
        if not paths:
            logger.warning("No YOLO images; skipping YOLO benchmark or set --yolo-images")
        else:
            logger.info("Benchmarking YOLO...")
            results["yolo"] = benchmark_yolo(paths, args.trials, batch_size=4)
    if args.db or args.all:
        logger.info("Benchmarking DB...")
        results["db"] = benchmark_db(n_ops=100, n_trials=args.trials)
    if args.api or args.all:
        logger.info("Benchmarking API...")
        import os
        base = os.environ.get("API_URL", "http://localhost:8000")
        results["api"] = benchmark_api(base, args.trials)

    print(json.dumps(results, indent=2))
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(results, indent=2), encoding="utf-8")
        logger.info("Results written to %s", args.output)

    sys.exit(0)


if __name__ == "__main__":
    main()
