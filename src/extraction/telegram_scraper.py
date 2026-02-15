"""Telegram channel scraper using Telethon/Telegram Client API."""

from datetime import datetime
from typing import Any

from src.logger import get_logger

logger = get_logger(__name__)


class TelegramScraper:
    """Scrape messages from Telegram channels. Requires Telethon and credentials."""

    def __init__(
        self,
        session_factory=None,
        limit_per_channel: int = 100,
        since: datetime | None = None,
    ):
        self.session_factory = session_factory
        self.limit_per_channel = limit_per_channel
        self.since = since

    def scrape_channels(self, channels: list[str]) -> dict[str, Any]:
        """Fetch messages from each channel. Returns {messages: [...], counts: {channel: n}}."""
        try:
            from telethon import TelegramClient , connection
            from telethon.tl.types import Message as TgMessage
            from src.config import get_settings
        except ImportError as e:
            logger.error("Telethon not installed: %s", e)
            return {"messages": [], "counts": {}}

        settings = get_settings()
        api_id = settings.telegram_api_id or ""
        api_hash = settings.telegram_api_hash or ""
        if not api_id or not api_hash:
            logger.error("TELEGRAM_API_ID and TELEGRAM_API_HASH required")
            return {"messages": [], "counts": {}}

        import asyncio

        async def _run():
            settings= get_settings()
            proxy_config = None
            if settings.telegram_proxy_addr:
                proxy_config = (
                    settings.telegram_proxy_addr, 
                    settings.telegram_proxy_port, 
                    settings.telegram_proxy_secret
                )

            client = TelegramClient(
                "medical_intel_session", 
                settings.telegram_api_id, 
                settings.telegram_api_hash,
                connection=connection.ConnectionTcpMTProxyRandomizedIntermediate,
                proxy=proxy_config  # Referencing environment details 
            )
            messages = []
            counts = {}
            try:
                await client.start()
                for ch in channels:
                    try:
                        msgs = await self._fetch_messages_async(client, ch)
                        messages.extend(msgs)
                        counts[ch] = len(msgs)
                    except Exception as e:
                        logger.warning("Channel %s: %s", ch, e)
                        counts[ch] = 0
                return messages, counts
            finally:
                await client.disconnect()

        messages, counts = asyncio.run(_run())
        if self.session_factory and messages:
            self._persist(messages)
        return {"messages": messages, "counts": counts}

    async def _fetch_messages_async(self, client, channel: str) -> list[dict]:
        from telethon.tl.types import Message as TgMessage

        out = []
        limit = self.limit_per_channel
        min_date = self.since
        async for m in client.iter_messages(channel, limit=limit, offset_date=min_date):
            if getattr(m, "message", None):
                out.append({
                    "channel_id": channel,
                    "external_id": str(m.id),
                    "text": m.message,
                    "date": m.date.isoformat() if getattr(m, "date", None) else None,
                    "raw": None,
                })
        return out

    def _persist(self, messages: list[dict]) -> None:
        from src.database.models import Message

        with self.session_factory() as session:
            for m in messages:
                rec = Message(
                    channel_id=m["channel_id"],
                    external_id=m["external_id"],
                    text=m.get("text"),
                    raw=m,
                )
                session.add(rec)
            session.commit()
