"""
CartMorph — Kroger store adapter.

Uses the Kroger API v1 for product search and cart operations.
Auth: OAuth 2.0 (Client Credentials or Authorization Code).
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from ..auth.oauth2 import OAuth2ClientCredentials, OAuth2AuthorizationCode
from ..auth.token_store import TokenStore
from ..utils.http_client import HttpClient
from ..utils.rate_limiter import RateLimiter
from ..unify.models import Cart, CartItem, Product
from ..unify.mapper import map_kroger_products
from .base import StoreAdapter

logger = logging.getLogger(__name__)

# Kroger maps location ID for product availability (default: generic)
DEFAULT_LOCATION_ID = "01400943"

# Header key used by Kroger to accept authorization
KROGER_AUTH_HEADER = "Authorization"


class KrogerAdapter(StoreAdapter):
    """Adapter for the Kroger API v1.

    Endpoints:
    - ``/products`` — search products by keyword
    - ``/products/{upc}`` — get product by UPC
    - ``/cart`` — manage the user's cart (auth code flow)
    """

    store_id = "kroger"
    store_name = "Kroger"

    def __init__(self, config: Dict[str, Any], token_store: Optional[TokenStore] = None):
        super().__init__(config)
        self._http: Optional[HttpClient] = None
        self._token_store = token_store
        self._client_credentials_auth: Optional[OAuth2ClientCredentials] = None
        self._auth_code_auth: Optional[OAuth2AuthorizationCode] = None

        rate_limit = config.get("rate_limit", {})
        self._limiter = RateLimiter(
            requests_per_second=rate_limit.get("requests_per_second"),
            requests_per_minute=rate_limit.get("requests_per_minute"),
        )

        self._setup_auth(config)

    def _setup_auth(self, config: Dict[str, Any]) -> None:
        """Initialize OAuth2 client credentials auth."""
        client_id = config.get("client_id", "")
        client_secret = config.get("client_secret", "")
        auth_url = config.get("auth_url", "")
        scopes = config.get("scopes", ["product.compact"])
        redirect_uri = config.get("redirect_uri", "")

        if not client_id or not client_secret:
            logger.warning("[kroger] Missing client_id or client_secret")
            return

        # Client credentials for product browsing
        if auth_url:
            self._client_credentials_auth = OAuth2ClientCredentials(
                client_id=client_id,
                client_secret=client_secret,
                token_url=auth_url,
                scopes=scopes,
            )

        # Authorization code for cart operations
        if redirect_uri:
            authorize_url = "https://api.kroger.com/v1/connect/oauth2/authorize"
            self._auth_code_auth = OAuth2AuthorizationCode(
                client_id=client_id,
                client_secret=client_secret,
                authorize_url=authorize_url,
                token_url=auth_url,
                redirect_uri=redirect_uri,
                scopes=scopes,
            )

    def _get_headers(self) -> Dict[str, str]:
        """Return headers with a valid access token."""
        if self._client_credentials_auth:
            return self._client_credentials_auth.to_auth_header()
        return {}

    def _get_http(self) -> HttpClient:
        if self._http is None:
            self._http = HttpClient(
                base_url=self._config.get("base_url", "https://api.kroger.com/v1"),
                headers=self._get_headers(),
            )
        return self._http

    def search_products(self, query: str, limit: int = 10) -> List[Product]:
        """Search Kroger products by keyword.

        GET /products?filter.term={query}&filter.limit={limit}
        """
        if not self.is_enabled:
            logger.debug("[kroger] Store disabled, skipping search")
            return []

        self._limiter.wait()
        http = self._get_http()

        params = {
            "filter.term": query,
            "filter.limit": limit,
        }

        loc_id = self._config.get("location_id", DEFAULT_LOCATION_ID)
        if loc_id:
            params["filter.locationId"] = loc_id

        try:
            resp = http.get("/products", params=params)
            data = resp.json()
        except Exception:
            logger.exception("[kroger] Product search failed for query='%s'", query)
            return []

        items = data.get("data", [])
        return map_kroger_products(items)

    def get_product(self, product_id: str) -> Optional[Product]:
        """Get a single Kroger product by UPC.

        GET /products/{upc}
        """
        if not self.is_enabled:
            return None

        self._limiter.wait()
        http = self._get_http()

        try:
            resp = http.get(f"/products/{product_id}")
            data = resp.json()
            items = data.get("data", [])
            if items:
                return map_kroger_products([items[0]])[0]
        except Exception:
            logger.exception("[kroger] Get product failed for id=%s", product_id)
        return None

    def get_authorization_url(self) -> Optional[str]:
        """Get the authorization URL for cart operations (auth code flow)."""
        if self._auth_code_auth:
            return self._auth_code_auth.get_authorization_url()
        return None

    def complete_authorization(self, code: str) -> bool:
        """Complete the auth code flow and obtain a cart token."""
        if not self._auth_code_auth:
            logger.error("[kroger] Authorization code flow not configured")
            return False
        try:
            entry = self._auth_code_auth.exchange_code(code)
            if self._token_store:
                self._token_store.set("kroger_cart", entry)
            logger.info("[kroger] Authorization code exchange successful")
            return True
        except Exception:
            logger.exception("[kroger] Authorization code exchange failed")
            return False

    def add_to_cart(self, product: Product, quantity: int = 1) -> bool:
        """Add a product to the user's Kroger cart (requires auth code flow).

        PUT /cart
        """
        if not self.is_enabled:
            return False

        cart_token = None
        if self._token_store:
            cart_token = self._token_store.get("kroger_cart")

        if not cart_token:
            logger.warning("[kroger] No cart token. Complete authorization code flow first.")
            return False

        self._limiter.wait()
        headers = {
            "Authorization": f"Bearer {cart_token}",
            "Content-Type": "application/json",
        }
        payload = {
            "items": [
                {
                    "upc": product.upc or product.sku,
                    "quantity": quantity,
                }
            ]
        }

        try:
            http = HttpClient(
                base_url=self._config.get("base_url", "https://api.kroger.com/v1"),
            )
            http.post("/cart", json=payload, headers=headers)
            logger.info("[kroger] Added '%s' (qty=%d) to cart", product.name, quantity)
            return True
        except Exception:
            logger.exception("[kroger] Add to cart failed for '%s'", product.name)
            return False

    def get_cart(self) -> Optional[Cart]:
        """Retrieve the current cart contents."""
        if not self.is_enabled:
            return None

        cart_token = None
        if self._token_store:
            cart_token = self._token_store.get("kroger_cart")

        if not cart_token:
            logger.warning("[kroger] No cart token. Complete authorization code flow first.")
            return None

        self._limiter.wait()
        headers = {"Authorization": f"Bearer {cart_token}"}

        try:
            http = HttpClient(
                base_url=self._config.get("base_url", "https://api.kroger.com/v1"),
            )
            resp = http.get("/cart", headers=headers)
            data = resp.json()
            cart = Cart(store_id=self.store_id, store_name=self.store_name)
            for item in data.get("data", {}).get("itemCount", []):
                # Minimal cart item mapping
                name = item.get("name", "Unknown Product")
                price = item.get("price", {})
                price_val = None
                if isinstance(price, dict):
                    price_val = price.get("regular")
                product = Product(
                    name=name,
                    price=float(price_val) if price_val else None,
                    store_id=self.store_id,
                    store_name=self.store_name,
                )
                cart.add_item(product, quantity=item.get("quantity", 1))
            return cart
        except Exception:
            logger.exception("[kroger] Get cart failed")
            return None

    def close(self) -> None:
        if self._http:
            self._http.close()
