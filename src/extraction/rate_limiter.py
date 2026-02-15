"""Rate limiting for Telegram API calls."""

import time
from threading import Lock


class TokenBucketRateLimiter:
    """Simple token bucket: refill_rate per second, capacity cap."""

    def __init__(self, refill_rate: float = 1.0, capacity: int = 30):
        self.refill_rate = refill_rate
        self.capacity = capacity
        self.tokens = float(capacity)
        self.last = time.monotonic()
        self._lock = Lock()

    def acquire(self) -> None:
        with self._lock:
            now = time.monotonic()
            self.tokens = min(self.capacity, self.tokens + (now - self.last) * self.refill_rate)
            self.last = now
            if self.tokens < 1:
                sleep = (1 - self.tokens) / self.refill_rate
                time.sleep(sleep)
                self.tokens = 0
                self.last = time.monotonic()
            else:
                self.tokens -= 1
