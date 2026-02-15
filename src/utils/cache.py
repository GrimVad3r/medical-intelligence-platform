"""Simple in-memory cache utilities."""

from functools import lru_cache
from typing import Any, Callable, TypeVar

T = TypeVar("T")


def cached(ttl_seconds: int = 300):
    """LRU cache with optional TTL (simplified: just use lru_cache)."""
    def deco(f: Callable[..., T]) -> Callable[..., T]:
        return lru_cache(maxsize=128)(f)  # type: ignore
    return deco
