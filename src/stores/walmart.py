"""
CartMorph — Walmart store adapter.

Uses the Walmart Marketplace / Grocery APIs for product search.
Auth: OAuth 2.0 (Client Credentials).
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from ..auth.oauth2 import OAuth2ClientCredentials
from ..utils.http_client import HttpClient
from ..utils.rate_limiter import RateLimiter
from ..unify.models import Product
from ..unify.mapper import map_walmart_products, map_walmart_product
from .base import StoreAdapter

logger = logging.getLogger(__name__)


class WalmartAdapter(StoreAdapter):
    """Adapter for the Walmart Marketplace / Grocery API.

    Endpoints:
    - ``/items`` — search products (Marketplace)
    - ``/feeds`` — product data feeds

    Note: Walmart's Marketplace API is primarily for sellers. For grocery
    browsing, this adapter uses the available product endpoints.
    """

    store_id = "walmart"
    store_name = "Walmart"

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self._http: Optional[HttpClient] = None
        self._auth: Optional[OAuth2ClientCredentials] = None

        rate_limit = config.get("rate_limit", {})
        self._limiter = RateLimiter(
            requests_per_second=rate_limit.get("requests_per_second"),
            requests_per_minute=rate_limit.get("requests_per_minute"),
        )

        self._setup_auth(config)

    def _setup_auth(self, config: Dict[str, Any]) -> None:
        client_id = config.get("client_id", "")
        client_secret = config.get("client_secret", "")
        auth_url = config.get("auth_url", "")

        if client_id and client_secret and auth_url:
            self._auth = OAuth2ClientCredentials(
                client_id=client_id,
                client_secret=client_secret,
                token_url=auth_url,
            )
        else:
            logger.warning("[walmart] Missing credentials or auth_url")

    def _get_headers(self) -> Dict[str, str]:
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        if self._auth:
            headers.update(self._auth.to_auth_header())
        return headers

    def _get_http(self) -> HttpClient:
        if self._http is None:
            self._http = HttpClient(
                base_url=self._config.get("base_url", "https://marketplace.walmartapis.com/v3"),
                headers=self._get_headers(),
            )
        return self._http

    def search_products(self, query: str, limit: int = 10) -> List[Product]:
        """Search Walmart products by keyword.

        GET /items?query={query}&limit={limit}
        """
        if not self.is_enabled:
            return []

        self._limiter.wait()
        http = self._get_http()

        params = {
            "query": query,
            "limit": limit,
        }

        try:
            resp = http.get("/items", params=params)
            data = resp.json()
        except Exception:
            logger.exception("[walmart] Product search failed for query='%s'", query)
            return []

        # Handle both list and dict response shapes
        items = []
        if isinstance(data, list):
            items = data
        elif isinstance(data, dict):
            items = data.get("items", []) or data.get("data", []) or []

        return map_walmart_products(items[:limit])

    def get_product(self, product_id: str) -> Optional[Product]:
        """Get a single Walmart product by ID.

        GET /items/{id}
        """
        if not self.is_enabled:
            return None

        self._limiter.wait()
        http = self._get_http()

        try:
            resp = http.get(f"/items/{product_id}")
            data = resp.json()
            items = data.get("items", []) if isinstance(data, dict) else [data]
            if items:
                return map_walmart_product(items[0])
        except Exception:
            logger.exception("[walmart] Get product failed for id=%s", product_id)
        return None

    def close(self) -> None:
        if self._http:
            self._http.close()
