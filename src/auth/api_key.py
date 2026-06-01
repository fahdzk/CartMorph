"""
CartMorph — API Key and Bearer Token authentication.

Simple wrapper for APIs that use a static API key or bearer token
sent in the ``Authorization`` header on every request.
"""

from __future__ import annotations

import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class ApiKeyAuth:
    """Authentication via a static API key or bearer token.

    Usage::

        auth = ApiKeyAuth(api_key="your-key-here")
        headers = auth.to_headers()
        # Pass headers to your HTTP client
    """

    def __init__(self, api_key: str, header_format: str = "Bearer {key}"):
        if not api_key or api_key.startswith("YOUR_"):
            logger.warning("ApiKeyAuth: placeholder API key detected. "
                           "Set a real key in cartmorph.config.yaml.")
        self._api_key = api_key
        self._header_format = header_format
        self._configured = not api_key.startswith("YOUR_")

    @property
    def is_configured(self) -> bool:
        """True if a real (non-placeholder) API key is set."""
        return self._configured

    def to_headers(self) -> Dict[str, str]:
        """Return the ``Authorization`` header dict."""
        return {"Authorization": self._header_format.format(key=self._api_key)}

    def __str__(self) -> str:
        if self._configured:
            masked = self._api_key[:4] + "..." + self._api_key[-4:]
            return f"ApiKeyAuth({masked})"
        return "ApiKeyAuth(NOT_CONFIGURED)"
