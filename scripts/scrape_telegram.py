#!/usr/bin/env python3
"""
Telegram scraper CLI for Medical Intelligence Platform.

Scrapes messages from configured Telegram channels, optionally runs NLP,
and persists to the database. Supports rate limiting and resume.
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime, timezone

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from src.logger import get_logger
    from src.config import get_settings
    from src.extraction.telegram_scraper import TelegramScraper
    from src.extraction.telegram_scraper_nlp import TelegramScraperNLP
    from src.database.connection import get_session_factory
except ImportError as e:
    print(f"Import error: {e}. Ensure src is on PYTHONPATH.", file=sys.stderr)
    sys.exit(1)

logger = get_logger(__name__)


def parse_channels(channel_arg: str) -> list[str]:
    """Parse comma-separated channel names/IDs."""
    return [c.strip() for c in channel_arg.split(",") if c.strip()]


def main():
    parser = argparse.ArgumentParser(
        description="Scrape Telegram channels for Medical Intelligence Platform."
    )
    parser.add_argument(
        "channels",
        nargs="?",
        default=None,
        help="Comma-separated channel usernames or IDs (or use config)",
    )
    parser.add_argument("--limit", type=int, default=1000, help="Max messages per channel")
    parser.add_argument("--since", type=str, default=None, help="ISO date (e.g. 2024-01-01)")
    parser.add_argument("--nlp", action="store_true", help="Run NLP pipeline on messages")
    parser.add_argument("--dry-run", action="store_true", help="Fetch only; do not persist")
    parser.add_argument("--save-json", type=Path, default=None, help="Save raw messages to JSON file")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose logging")
    args = parser.parse_args()

    settings = get_settings()
    channel_list = parse_channels(args.channels) if args.channels else getattr(
        settings, "telegram_channels", []
    )
    if not channel_list:
        logger.error("No channels specified. Use positional arg or set telegram_channels in config.")
        sys.exit(1)

    since_dt = None
    if args.since:
        try:
            since_dt = datetime.fromisoformat(args.since.replace("Z", "+00:00"))
            if since_dt.tzinfo is None:
                since_dt = since_dt.replace(tzinfo=timezone.utc)
        except ValueError:
            logger.error("Invalid --since date: %s", args.since)
            sys.exit(1)

    session_factory = None if args.dry_run else get_session_factory()
    scraper_class = TelegramScraperNLP if args.nlp else TelegramScraper

    try:
        scraper = scraper_class(
            session_factory=session_factory,
            limit_per_channel=args.limit,
            since=since_dt,
        )
        results = scraper.scrape_channels(channel_list)
    except Exception as e:
        logger.exception("Scraping failed: %s", e)
        sys.exit(1)

    if args.save_json:
        import json
        args.save_json.parent.mkdir(parents=True, exist_ok=True)
        with open(args.save_json, "w", encoding="utf-8") as f:
            json.dump(results.get("messages", []), f, indent=2, default=str)
        logger.info("Saved %d messages to %s", len(results.get("messages", [])), args.save_json)

    total = sum(results.get("counts", {}).values())
    logger.info("Scrape complete. Total messages: %d (dry_run=%s)", total, args.dry_run)
    sys.exit(0)


if __name__ == "__main__":
    main()
