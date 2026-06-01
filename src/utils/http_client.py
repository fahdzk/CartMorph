"""
CartMorph — Shared HTTP client with retry + backoff.
"""

from __future__ import annotations

import time
import logging
from typing import Any, Dict, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


class HttpClient:
    """Shared HTTP client with automatic retry, backoff, and error handling.

    Features:
    - Configurable retry with exponential backoff on 429/5xx responses.
    - Automatic ``Retry-After`` header respect on 429 responses.
    - Per-request timeout with a sensible default.
    - Session reuse for connection pooling.
    """

    DEFAULT_TIMEOUT = 30  # seconds
    DEFAULT_MAX_RETRIES = 3
    DEFAULT_BACKOFF_FACTOR = 1.0

    def __init__(
        self,
        base_url: str = "",
        headers: Optional[Dict[str, str]] = None,
        timeout: int = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        backoff_factor: float = DEFAULT_BACKOFF_FACTOR,
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()

        if headers:
            self.session.headers.update(headers)

        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=backoff_factor,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
            respect_retry_after_header=True,
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

    def _url(self, path: str) -> str:
        if path.startswith("http://") or path.startswith("https://"):
            return path
        path = path if path.startswith("/") else f"/{path}"
        return f"{self.base_url}{path}"

    def get(
        self,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> requests.Response:
        url = self._url(path)
        logger.debug("GET %s params=%s", url, params)
        resp = self.session.get(url, params=params, headers=headers, timeout=self.timeout)
        self._raise_for_status(resp)
        return resp

    def post(
        self,
        path: str,
        data: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> requests.Response:
        url = self._url(path)
        logger.debug("POST %s", url)
        resp = self.session.post(url, data=data, json=json, headers=headers, timeout=self.timeout)
        self._raise_for_status(resp)
        return resp

    def _raise_for_status(self, resp: requests.Response) -> None:
        if resp.status_code == 429:
            retry_after = resp.headers.get("Retry-After", "unknown")
            logger.warning(
                "429 Too Many Requests — Retry-After: %s (URL: %s)",
                retry_after,
                resp.url,
            )
        resp.raise_for_status()

    def close(self) -> None:
        self.session.close()

    def __enter__(self) -> "HttpClient":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()
