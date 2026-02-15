"""Telegram scraper with inline NLP processing."""

from datetime import datetime
from typing import Any

from src.extraction.telegram_scraper import TelegramScraper
from src.logger import get_logger

logger = get_logger(__name__)


class TelegramScraperNLP(TelegramScraper):
    """Scraper that runs NLP on each message before persisting."""

    def _persist(self, messages: list[dict]) -> None:
        try:
            from src.nlp.message_processor import MessageProcessor
            from src.nlp.model_manager import ModelManager
        except ImportError:
            super()._persist(messages)
            return

        manager = ModelManager()
        processor = MessageProcessor(model_manager=manager)
        from src.database.models import Message, NLPResult

        with self.session_factory() as session:
            for m in messages:
                msg_rec = Message(
                    channel_id=m["channel_id"],
                    external_id=m["external_id"],
                    text=m.get("text"),
                    raw=m,
                )
                session.add(msg_rec)
                session.flush()
                try:
                    result = processor.process(m.get("text") or "", include_explanations=False)
                    nlp_rec = NLPResult(
                        message_id=msg_rec.id,
                        entities=result.get("entities", {}),
                        category=result.get("category"),
                        confidence=result.get("confidence"),
                        linked_entities=result.get("linked_entities", {}),
                    )
                    session.add(nlp_rec)
                    msg_rec.processed_nlp = 1
                except Exception as e:
                    logger.warning("NLP skip message %s: %s", m.get("external_id"), e)
            session.commit()
