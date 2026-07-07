"""Simple in-memory sliding-window rate limiter for auth endpoints."""
from __future__ import annotations
import time
from collections import defaultdict

class RateLimiter:
    def __init__(self):
        self._buckets: dict[str, list[float]] = defaultdict(list)

    def check(self, key: str, max_requests: int = 5, window_seconds: float = 60.0) -> bool:
        now = time.time()
        window_start = now - window_seconds
        self._buckets[key] = [t for t in self._buckets[key] if t > window_start]
        if len(self._buckets[key]) >= max_requests:
            return False
        self._buckets[key].append(now)
        return True

_rate_limiter = RateLimiter()

def get_rate_limiter() -> RateLimiter:
    return _rate_limiter
