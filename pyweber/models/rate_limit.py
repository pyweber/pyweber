"""In-memory token-bucket rate limiting."""

from __future__ import annotations

import os
import threading
import time
from dataclasses import dataclass, field

from pyweber.config.config import config


@dataclass
class _Bucket:
    tokens: float
    updated_at: float


@dataclass
class RateLimiter:
    rate_per_minute: float = 120.0
    burst: float | None = None
    _buckets: dict[str, _Bucket] = field(default_factory=dict)
    _lock: threading.Lock = field(default_factory=threading.Lock)

    def __post_init__(self):
        if self.burst is None:
            self.burst = max(self.rate_per_minute / 6, 1.0)

    @property
    def refill_per_second(self) -> float:
        return self.rate_per_minute / 60.0

    def allow(self, key: str) -> tuple[bool, float]:
        """Return (allowed, retry_after_seconds)."""
        now = time.monotonic()
        with self._lock:
            bucket = self._buckets.get(key)
            if bucket is None:
                bucket = _Bucket(tokens=self.burst, updated_at=now)
                self._buckets[key] = bucket

            elapsed = now - bucket.updated_at
            bucket.tokens = min(self.burst, bucket.tokens + elapsed * self.refill_per_second)
            bucket.updated_at = now

            if bucket.tokens >= 1.0:
                bucket.tokens -= 1.0
                return True, 0.0

            missing = 1.0 - bucket.tokens
            retry = missing / self.refill_per_second if self.refill_per_second else 60.0
            return False, max(retry, 0.1)


def rate_limit_enabled() -> bool:
    env = os.environ.get('PYWEBER_RATE_LIMIT_ENABLED')
    if env is not None:
        return env.strip().lower() in {'1', 'true', 'yes', 'on'}
    value = config.get('security', 'rate_limit_enabled', default=False)
    if isinstance(value, str):
        return value.strip().lower() in {'1', 'true', 'yes', 'on'}
    return bool(value)


def get_rate_limit_rpm() -> float:
    value = os.environ.get('PYWEBER_RATE_LIMIT_RPM') or config.get(
        'security', 'rate_limit_rpm', default=120
    )
    try:
        return float(value)
    except (TypeError, ValueError):
        return 120.0


_default_limiter: RateLimiter | None = None


def get_rate_limiter() -> RateLimiter:
    global _default_limiter
    rpm = get_rate_limit_rpm()
    if _default_limiter is None or _default_limiter.rate_per_minute != rpm:
        _default_limiter = RateLimiter(rate_per_minute=rpm)
    return _default_limiter
