"""
CartMorph — Abstract base class for store adapters.

Every store adapter (Kroger, Walmart, Instacart, Target, Custom)
must subclass ``StoreAdapter`` and implement the required methods.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from ..unify.models import Cart, Product, StoreInfo

logger = logging.getLogger(__name__)


class StoreAdapter(ABC):
    """Base class that all store adapters must implement.

    Subclasses must define:
    - ``store_id``: short string identifier (e.g. ``"kroger"``)
    - ``store_name``: human-readable name (e.g. ``"Kroger"``)
    - ``search_products()``: product search
    - ``get_product()``: single product lookup
    """

    store_id: str = ""
    store_name: str = ""

    def __init__(self, config: Dict[str, Any]):
        self._config = config
        self._enabled = config.get("enabled", False)
        self._base_url = config.get("base_url", "")

    @property
    def is_enabled(self) -> bool:
        return self._enabled

    @property
    def info(self) -> StoreInfo:
        return StoreInfo(
            store_id=self.store_id,
            name=self.store_name,
            base_url=self._base_url,
            auth_type=self._config.get("auth_type", "none"),
            enabled=self._enabled,
            portal_url=self._config.get("portal_url"),
            notes=self._config.get("notes"),
        )

    # ---- Abstract methods that all stores must implement ----

    @abstractmethod
    def search_products(self, query: str, limit: int = 10) -> List[Product]:
        """Search for products by keyword.

        Args:
            query: Search term (e.g. "milk", "bread")
            limit: Maximum number of results to return

        Returns:
            List of unified ``Product`` instances
        """
        ...

    @abstractmethod
    def get_product(self, product_id: str) -> Optional[Product]:
        """Look up a single product by its store-specific ID.

        Args:
            product_id: Store-specific product identifier (SKU, UPC, etc.)

        Returns:
            A unified ``Product`` or ``None`` if not found
        """
        ...

    # ---- Optional methods (not all stores support cart) ----

    def get_cart(self) -> Optional[Cart]:
        """Get the current cart state. Default: not supported."""
        logger.warning("[%s] Cart retrieval not implemented", self.store_id)
        return None

    def add_to_cart(self, product: Product, quantity: int = 1) -> bool:
        """Add a product to the cart. Default: not supported."""
        logger.warning("[%s] Add-to-cart not implemented", self.store_id)
        return False
