#!/usr/bin/env python3
"""
NLP analysis script for Medical Intelligence Platform.

Runs NER, classification, entity linking, and optional SHAP explainability
on text input or on messages from the database.
"""

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from src.logger import get_logger
    from src.nlp.message_processor import MessageProcessor
    from src.nlp.model_manager import ModelManager
    from src.database.connection import get_session_factory
    from src.database.queries import get_unprocessed_messages
except ImportError as e:
    print(f"Import error: {e}. Ensure src is on PYTHONPATH.", file=sys.stderr)
    sys.exit(1)

logger = get_logger(__name__)


def analyze_text(processor: MessageProcessor, text: str, explain: bool = False) -> dict:
    """Run full NLP pipeline on a single text. Returns result dict."""
    result = processor.process(text, include_explanations=explain)
    return result


def analyze_from_db(
    processor: MessageProcessor,
    session_factory,
    limit: int = 100,
    explain: bool = False,
) -> int:
    """Process unprocessed messages from DB. Returns count processed."""
    with session_factory() as session:
        messages = get_unprocessed_messages(session, limit=limit)
    count = 0
    for msg in messages:
        try:
            processor.process(msg.text, include_explanations=explain)
            count += 1
        except Exception as e:
            logger.warning("Skip message id=%s: %s", getattr(msg, "id", "?"), e)
    return count


def main():
    parser = argparse.ArgumentParser(
        description="Run NLP analysis (NER, classification, entity linking) for Medical Intelligence Platform."
    )
    parser.add_argument("--text", type=str, help="Analyze this text directly")
    parser.add_argument("--file", type=Path, help="Read text from file (one message per line or JSON list)")
    parser.add_argument("--from-db", action="store_true", help="Process unprocessed messages from database")
    parser.add_argument("--limit", type=int, default=100, help="Max messages when using --from-db")
    parser.add_argument("--explain", action="store_true", help="Include SHAP explanations (slower)")
    parser.add_argument("--preload-models", action="store_true", help="Preload models before processing")
    args = parser.parse_args()

    if not any([args.text, args.file, args.from_db]):
        parser.error("Provide one of: --text, --file, or --from-db")

    try:
        model_manager = ModelManager()
        if args.preload_models:
            model_manager.load_all()
        processor = MessageProcessor(model_manager=model_manager)
    except Exception as e:
        logger.exception("Failed to initialize NLP: %s", e)
        sys.exit(1)

    processed = 0
    if args.text:
        out = analyze_text(processor, args.text, explain=args.explain)
        print(out)  # or serialize to JSON
        processed = 1
    elif args.file:
        if not args.file.exists():
            logger.error("File not found: %s", args.file)
            sys.exit(1)
        content = args.file.read_text(encoding="utf-8")
        try:
            import json
            lines = json.loads(content) if content.strip().startswith("[") else content.strip().splitlines()
        except Exception:
            lines = content.strip().splitlines()
        for line in lines:
            if isinstance(line, dict):
                line = line.get("text", str(line))
            if not line:
                continue
            analyze_text(processor, line, explain=args.explain)
            processed += 1
        logger.info("Processed %d lines from %s", processed, args.file)
    elif args.from_db:
        session_factory = get_session_factory()
        processed = analyze_from_db(processor, session_factory, limit=args.limit, explain=args.explain)
        logger.info("Processed %d messages from database", processed)

    sys.exit(0)


if __name__ == "__main__":
    main()
