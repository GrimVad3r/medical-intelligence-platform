"""Validation utilities."""

import re


def is_valid_channel_id(channel: str) -> bool:
    return bool(channel and re.match(r"^[a-zA-Z0-9_]+$", channel))
