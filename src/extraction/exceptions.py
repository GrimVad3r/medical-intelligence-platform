"""Extraction-specific exceptions."""


class ExtractionError(Exception):
    """Base for extraction errors."""


class RateLimitError(ExtractionError):
    """Telegram rate limit hit."""


class ChannelAccessError(ExtractionError):
    """Cannot access channel."""
