"""
CartMorph — Generic adapter for custom/unofficial store integrations.

Handles any store configured via the ``custom_stores`` array in the config.
Supports all auth types: api_key, bearer, oauth2, basic, none.
"""

from __future__ import annotations

import logging
import base64
from typing import Any, Dict, List, Optional

from ..auth.api_key import ApiKeyAuth
from ..auth.oauth2 import OAuth2ClientCredentials
from ..utils.http_client import HttpClient
from ..utils.rate_limiter import RateLimiter
from ..unify.models import Product
from .base import StoreAdapter

logger = logging.getLogger(__name__)


class CustomStoreAdapter(StoreAdapter):
    """Generic adapter for stores configured via ``custom_stores``.

    This adapter does minimal product mapping — it stores the raw
    API responses in ``Product.raw`` for the caller to handle.
    Use the mapper module for more sophisticated field extraction.
    """

    def __init__(self, config: Dict[str, Any]):
        self._custom_config = config
        super().__init__(config)
        self.store_id = config.get("name", "custom").lower().replace(" ", "_")
        self.store_name = config.get("name", "Custom Store")
        self._http: Optional[HttpClient] = None
        self._auth_handler: Optional[Any] = None
        self._auth_type = config.get("auth_type", "none")

        rate_limit = config.get("rate_limit", {})
        self._limiter = RateLimiter(
            requests_per_second=rate_limit.get("requests_per_second"),
            requests_per_minute=rate_limit.get("requests_per_minute"),
        )

        self._setup_auth(config)

    def _setup_auth(self, config: Dict[str, Any]) -> None:
        auth_type = config.get("auth_type", "none")
        custom_headers = config.get("custom_headers", {})

        if auth_type == "api_key":
            api_key = config.get("api_key", "")
            self._auth_handler = ApiKeyAuth(api_key=api_key)
        elif auth_type == "bearer":
            api_key = config.get("api_key", "")
            self._auth_handler = ApiKeyAuth(api_key=api_key, header_format="Bearer {key}")
        elif auth_type == "oauth2":
            client_id = config.get("client_id", "")
            client_secret = config.get("client_secret", "")
            auth_url = config.get("auth_url", "")
            if client_id and client_secret and auth_url:
                self._auth_handler = OAuth2ClientCredentials(
                    client_id=client_id,
                    client_secret=client_secret,
                    token_url=auth_url,
                )
        elif auth_type == "basic":
            username = config.get("client_id", "")
            password = config.get("client_secret", "")
            credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
            self._auth_handler = {"Authorization": f"Basic {credentials}"}
        # auth_type == "none" : no setup needed

    def _get_headers(self) -> Dict[str, str]:
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        headers.update(self._custom_config.get("custom_headers", {}))

        if self._auth_handler is None:
            return headers

        if isinstance(self._auth_handler, dict):
            headers.update(self._auth_handler)
        elif hasattr(self._auth_handler, "to_headers"):
            headers.update(self._auth_handler.to_headers())
        elif hasattr(self._auth_handler, "to_auth_header"):
            headers.update(self._auth_handler.to_auth_header())

        return headers

    def _get_http(self) -> HttpClient:
        if self._http is None:
            self._http = HttpClient(
                base_url=self._config.get("base_url"),
                headers=self._get_headers(),
            )
        return self._http

    def search_products(self, query: str, limit: int = 10) -> List[Product]:
        """Search products using the custom store's API.

        This is a generic implementation. Stores with non-standard search
        endpoints should override this method.
        """
        if not self.is_enabled:
            return []

        self._limiter.wait()
        http = self._get_http()

        # Generic search attempt — most APIs use a "search" or "products" endpoint
        search_paths = self._custom_config.get("search_paths", ["/search", "/products", "/api/v1/search"])

        for path in search_paths:
            try:
                resp = http.get(path, params={"q": query, "query": query, "limit": limit})
                data = resp.json()
                break
            except Exception:
                logger.debug("[custom:%s] Search path '%s' failed, trying next", self.store_id, path)
                continue
        else:
            logger.error("[custom:%s] All search paths failed for query='%s'", self.store_id, query)
            return []

        items = []
        if isinstance(data, list):
            items = data
        elif isinstance(data, dict):
            items = (
                data.get("results", [])
                or data.get("products", [])
                or data.get("data", [])
                or data.get("items", [])
            )

        products = []
        for raw in items[:limit]:
            product = Product(
                name=raw.get("name") or raw.get("title") or "Unknown Product",
                price=raw.get("price"),
                sku=str(raw.get("id") or raw.get("sku") or ""),
                upc=raw.get("upc", ""),
                brand=raw.get("brand", ""),
                image_url=raw.get("image") or raw.get("image_url") or raw.get("thumbnail"),
                store_id=self.store_id,
                store_name=self.store_name,
                raw=raw,
            )
            products.append(product)
        return products

    def get_product(self, product_id: str) -> Optional[Product]:
        """Get a single product by ID using the custom store's API."""
        if not self.is_enabled:
            return None

        self._limiter.wait()
        http = self._get_http()

        # Try common product endpoint patterns
        for path_template in ["/products/{id}", "/api/v1/products/{id}", "/items/{id}"]:
            try:
                resp = http.get(path_template.format(id=product_id))
                data = resp.json()
                if data:
                    return Product(
                        name=data.get("name") or data.get("title") or "Unknown Product",
                        price=data.get("price"),
                        sku=str(data.get("id") or data.get("sku") or product_id),
                        upc=data.get("upc", ""),
                        brand=data.get("brand", ""),
                        image_url=data.get("image") or data.get("image_url"),
                        store_id=self.store_id,
                        store_name=self.store_name,
                        raw=data,
                    )
            except Exception:
                logger.debug("[custom:%s] Product path '%s' failed", self.store_id, path_template)
        return None

    def close(self) -> None:
        if self._http:
            self._http.close()
