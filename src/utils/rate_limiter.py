"""
CartMorph — Per-store rate limiter using a token-bucket algorithm.
"""

from __future__ import annotations

import time
import threading
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class RateLimiter:
    """Thread-safe token-bucket rate limiter.

    Usage::

        limiter = RateLimiter(requests_per_second=5)
        limiter.wait()  # blocks until a token is available
        # ... make API call ...
    """

    def __init__(self, requests_per_second: Optional[float] = None, requests_per_minute: Optional[int] = None):
        if requests_per_second is not None:
            self._rate = requests_per_second
            self._per_second = True
        elif requests_per_minute is not None:
            self._rate = requests_per_minute / 60.0
            self._per_second = False
        else:
            # Default: no rate limiting
            self._rate = None
            self._per_second = True

        self._min_interval = 1.0 / self._rate if self._rate else 0.0
        self._lock = threading.Lock()
        self._last_call = 0.0

    def wait(self) -> None:
        """Block until the next request is allowed under the rate limit."""
        if self._rate is None:
            return

        with self._lock:
            now = time.monotonic()
            elapsed = now - self._last_call
            wait_time = self._min_interval - elapsed
            if wait_time > 0:
                logger.debug("Rate limiter: waiting %.2fs", wait_time)
                time.sleep(wait_time)
            self._last_call = time.monotonic()

    @property
    def rate_description(self) -> str:
        if self._rate is None:
            return "unlimited"
        if self._per_second:
            return f"{self._rate} req/sec"
        return f"{int(self._rate * 60)} req/min"
