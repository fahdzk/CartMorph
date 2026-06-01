"""
CartMorph — Target RedSky adapter (unofficial).

Uses the Target RedSky internal API for product data.
Auth: None required for public product endpoints.

WARNING: This is an unofficial/semi-public API. Use responsibly and
respect rate limits.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from ..utils.http_client import HttpClient
from ..utils.rate_limiter import RateLimiter
from ..unify.models import Product
from ..unify.mapper import map_target_products, map_target_product
from .base import StoreAdapter

logger = logging.getLogger(__name__)


class TargetAdapter(StoreAdapter):
    """Adapter for the Target RedSky product API.

    Endpoints:
    - ``/redsky_aggregations/v1/web/pdp_v1`` — product detail
    - ``/redsky_aggregations/v1/web/plp_search_v1`` — product search
    """

    store_id = "target"
    store_name = "Target"

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self._http: Optional[HttpClient] = None

        # Conservative rate limiting for unofficial API
        rate_limit = config.get("rate_limit", {})
        self._limiter = RateLimiter(
            requests_per_second=rate_limit.get("requests_per_second", 5),
            requests_per_minute=rate_limit.get("requests_per_minute"),
        )

        # RedSky uses a guest key for public endpoints
        self._guest_key = config.get("guest_key", "9f3460af564d510d76da84d491e8191f")

    def _get_headers(self) -> Dict[str, str]:
        return {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "CartMorph/1.0",
        }

    def _get_http(self) -> HttpClient:
        if self._http is None:
            self._http = HttpClient(
                base_url=self._config.get("base_url", "https://redsky.target.com"),
                headers=self._get_headers(),
            )
        return self._http

    def search_products(self, query: str, limit: int = 10) -> List[Product]:
        """Search Target products by keyword using RedSky PLP search.

        GET /redsky_aggregations/v1/web/plp_search_v1
        """
        if not self.is_enabled:
            return []

        self._limiter.wait()
        http = self._get_http()

        params = {
            "key": self._guest_key,
            "keyword": query,
            "count": limit,
            "offset": 0,
            "default_purchasability_filter": "true",
        }

        try:
            resp = http.get("/redsky_aggregations/v1/web/plp_search_v1", params=params)
            data = resp.json()
        except Exception:
            logger.exception("[target] Product search failed for query='%s'", query)
            return []

        items = []
        search_results = data.get("search_response", {})
        if isinstance(search_results, dict):
            items_list = search_results.get("items", {})
            if isinstance(items_list, dict):
                items = items_list.get("Item", [])
            elif isinstance(items_list, list):
                items = items_list

        return map_target_products(items[:limit])

    def get_product(self, product_id: str) -> Optional[Product]:
        """Get a single Target product by Tcin (Target Catalogue ID).

        GET /redsky_aggregations/v1/web/pdp_v1?tcin={id}
        """
        if not self.is_enabled:
            return None

        self._limiter.wait()
        http = self._get_http()

        params = {
            "key": self._guest_key,
            "tcin": product_id,
            "pricing_store_id": "3991",
        }

        try:
            resp = http.get("/redsky_aggregations/v1/web/pdp_v1", params=params)
            data = resp.json()
            product_data = data.get("product", {})
            all_data = product_data.get("item", product_data) if isinstance(product_data, dict) else {}
            if all_data:
                return map_target_product(all_data)
        except Exception:
            logger.exception("[target] Get product failed for id=%s", product_id)
        return None

    def close(self) -> None:
        if self._http:
            self._http.close()
