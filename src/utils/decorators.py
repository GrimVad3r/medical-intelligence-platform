"""Retry, timeout, and logging decorators."""

import functools
import time
from typing import Callable, TypeVar

from src.logger import get_logger

F = TypeVar("F", bound=Callable)
logger = get_logger(__name__)


def retry(max_attempts: int = 3, delay: float = 1.0):
    def deco(f: F) -> F:
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            last = None
            for i in range(max_attempts):
                try:
                    return f(*args, **kwargs)
                except Exception as e:
                    last = e
                    if i < max_attempts - 1:
                        time.sleep(delay)
            raise last
        return wrapper  # type: ignore
    return deco


def log_duration(name: str):
    def deco(f: F) -> F:
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            start = time.perf_counter()
            try:
                return f(*args, **kwargs)
            finally:
                logger.info("%s took %.3fs", name, time.perf_counter() - start)
        return wrapper  # type: ignore
    return deco
