"""
CartMorph — Token store with expiry tracking and automatic refresh.

Caches OAuth tokens in memory, tracks expiry, and transparently
refreshes when a token is expired or about to expire.
"""

from __future__ import annotations

import time
import logging
import threading
from dataclasses import dataclass, field
from typing import Callable, Dict, Optional

logger = logging.getLogger(__name__)

# Refresh tokens 60 seconds before actual expiry to avoid race conditions
DEFAULT_EXPIRY_BUFFER = 60


@dataclass
class TokenEntry:
    """A single cached token with its metadata."""
    access_token: str
    token_type: str = "Bearer"
    expires_at: float = 0.0          # unix timestamp
    refresh_token: Optional[str] = None
    fetched_at: float = field(default_factory=time.time)

    @property
    def is_expired(self) -> bool:
        if self.expires_at <= 0:
            return False  # no expiry info, assume static token
        return time.time() >= self.expires_at

    @property
    def is_stale(self) -> bool:
        """True if the token should be proactively refreshed."""
        if self.expires_at <= 0:
            return False
        return time.time() >= (self.expires_at - DEFAULT_EXPIRY_BUFFER)


class TokenStore:
    """Thread-safe in-memory token cache with background refresh support.

    Usage::

        store = TokenStore()
        store.set_fetcher("kroger", lambda: fetch_kroger_token())
        token = store.get("kroger")  # auto-refreshes if stale
    """

    def __init__(self):
        self._tokens: Dict[str, TokenEntry] = {}
        self._fetchers: Dict[str, Callable[[], TokenEntry]] = {}
        self._lock = threading.Lock()

    def set_fetcher(self, key: str, fetcher: Callable[[], TokenEntry]) -> None:
        """Register a token fetcher function for a given key."""
        self._fetchers[key] = fetcher

    def get(self, key: str) -> Optional[str]:
        """Return a valid access token, refreshing if stale/expired.

        Returns ``None`` if no fetcher is registered for the key.
        """
        with self._lock:
            entry = self._tokens.get(key)
            if entry and not entry.is_stale:
                return entry.access_token

            fetcher = self._fetchers.get(key)
            if fetcher is None:
                logger.warning("No token fetcher registered for '%s'", key)
                return entry.access_token if entry else None

            # Refresh
            try:
                logger.info("Refreshing token for '%s'", key)
                new_entry = fetcher()
                self._tokens[key] = new_entry
                return new_entry.access_token
            except Exception:
                logger.exception("Token refresh failed for '%s'", key)
                # Return stale token as fallback; caller will handle auth errors
                return entry.access_token if entry else None

    def set(self, key: str, entry: TokenEntry) -> None:
        """Manually set a token entry."""
        with self._lock:
            self._tokens[key] = entry

    def invalidate(self, key: str) -> None:
        """Remove a cached token, forcing a refresh on next access."""
        with self._lock:
            self._tokens.pop(key, None)

    def clear(self) -> None:
        """Clear all cached tokens."""
        with self._lock:
            self._tokens.clear()

    def status(self) -> Dict[str, dict]:
        """Return a snapshot of all cached tokens and their status."""
        result = {}
        with self._lock:
            for key, entry in self._tokens.items():
                result[key] = {
                    "has_token": bool(entry.access_token),
                    "token_type": entry.token_type,
                    "expires_at": entry.expires_at,
                    "is_expired": entry.is_expired,
                    "is_stale": entry.is_stale,
                    "fetched_at": entry.fetched_at,
                }
        return result
