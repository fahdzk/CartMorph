"""
CartMorph — Instacart store adapter.

Supports both the Developer Platform (API Key) and Connect APIs (OAuth 2.0).
Auth: API Key (Bearer) or OAuth 2.0 Client Credentials.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from ..auth.api_key import ApiKeyAuth
from ..auth.oauth2 import OAuth2ClientCredentials
from ..utils.http_client import HttpClient
from ..utils.rate_limiter import RateLimiter
from ..unify.models import Product
from ..unify.mapper import map_instacart_products, map_instacart_product
from .base import StoreAdapter

logger = logging.getLogger(__name__)


class InstacartAdapter(StoreAdapter):
    """Adapter for the Instacart Developer Platform / Connect API.

    Developer Platform uses API Key auth.
    Connect API uses OAuth 2.0 Client Credentials.

    Both use the same base URL pattern with different auth headers.
    """

    store_id = "instacart"
    store_name = "Instacart"

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self._http: Optional[HttpClient] = None
        self._api_key_auth: Optional[ApiKeyAuth] = None
        self._oauth2_auth: Optional[OAuth2ClientCredentials] = None
        self._use_oauth2 = False

        rate_limit = config.get("rate_limit", {})
        self._limiter = RateLimiter(
            requests_per_second=rate_limit.get("requests_per_second"),
            requests_per_minute=rate_limit.get("requests_per_minute"),
        )

        self._setup_auth(config)

    def _setup_auth(self, config: Dict[str, Any]) -> None:
        # Prefer OAuth2 (Connect API) if credentials are present
        client_id = config.get("client_id", "")
        client_secret = config.get("client_secret", "")

        if client_id and client_secret:
            self._use_oauth2 = True
            auth_url = config.get("base_url", "https://connect.instacart.com")
            self._oauth2_auth = OAuth2ClientCredentials(
                client_id=client_id,
                client_secret=client_secret,
                token_url=f"{auth_url}/oauth/token",
            )
            logger.info("[instacart] Using Connect API (OAuth 2.0) auth")
        else:
            # Fall back to API key (Developer Platform)
            api_key = config.get("api_key", "")
            self._api_key_auth = ApiKeyAuth(api_key=api_key)
            if self._api_key_auth.is_configured:
                logger.info("[instacart] Using Developer Platform (API Key) auth")
            else:
                logger.warning("[instacart] No valid API key or OAuth2 credentials configured")

    def _get_headers(self) -> Dict[str, str]:
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        if self._use_oauth2 and self._oauth2_auth:
            headers.update(self._oauth2_auth.to_auth_header())
        elif self._api_key_auth:
            headers.update(self._api_key_auth.to_headers())
        return headers

    def _get_http(self) -> HttpClient:
        if self._http is None:
            self._http = HttpClient(
                base_url=self._config.get("base_url", "https://connect.instacart.com"),
                headers=self._get_headers(),
            )
        return self._http

    def search_products(self, query: str, limit: int = 10) -> List[Product]:
        """Search Instacart products by keyword.

        GET /api/v1/products?query={query}&limit={limit}
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
            resp = http.get("/api/v1/products", params=params)
            data = resp.json()
        except Exception:
            logger.exception("[instacart] Product search failed for query='%s'", query)
            return []

        items = []
        if isinstance(data, list):
            items = data
        elif isinstance(data, dict):
            items = data.get("products", []) or data.get("data", []) or data.get("results", [])

        return map_instacart_products(items[:limit])

    def get_product(self, product_id: str) -> Optional[Product]:
        """Get a single Instacart product by ID.

        GET /api/v1/products/{id}
        """
        if not self.is_enabled:
            return None

        self._limiter.wait()
        http = self._get_http()

        try:
            resp = http.get(f"/api/v1/products/{product_id}")
            data = resp.json()
            items = [data] if not isinstance(data, list) else data
            if items:
                return map_instacart_product(items[0])
        except Exception:
            logger.exception("[instacart] Get product failed for id=%s", product_id)
        return None

    def close(self) -> None:
        if self._http:
            self._http.close()
