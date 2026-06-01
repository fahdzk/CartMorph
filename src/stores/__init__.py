"""
CartMorph — Store registry and factory.

Discovers, instantiates, and manages all enabled store adapters
from the loaded configuration.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from ..config_loader import get_enabled_stores, get_enabled_custom_stores
from ..auth.token_store import TokenStore
from .base import StoreAdapter
from .kroger import KrogerAdapter
from .walmart import WalmartAdapter
from .instacart import InstacartAdapter
from .target import TargetAdapter
from .custom import CustomStoreAdapter

logger = logging.getLogger(__name__)

# Map store IDs -> adapter classes
BUILTIN_ADAPTERS: Dict[str, type] = {
    "kroger": KrogerAdapter,
    "walmart": WalmartAdapter,
    "instacart": InstacartAdapter,
    "target": TargetAdapter,
}


class StoreRegistry:
    """Manages all store adapter instances.

    Usage::

        registry = StoreRegistry(config, token_store)
        registry.discover()
        products = registry.search_all("milk", limit=5)
    """

    def __init__(self, config: Dict[str, Any], token_store: Optional[TokenStore] = None):
        self._config = config
        self._token_store = token_store or TokenStore()
        self._adapters: Dict[str, StoreAdapter] = {}
        self._custom_adapters: Dict[str, CustomStoreAdapter] = {}

    def discover(self) -> int:
        """Instantiate all enabled adapters from config. Returns count of enabled stores."""
        enabled_stores = get_enabled_stores(self._config)

        for store_id, store_cfg in enabled_stores.items():
            adapter_cls = BUILTIN_ADAPTERS.get(store_id)
            if adapter_cls is None:
                logger.warning("No adapter registered for store '%s'", store_id)
                continue
            try:
                # Kroger needs the token_store for cart operations
                if store_id == "kroger":
                    adapter = adapter_cls(store_cfg, token_store=self._token_store)
                else:
                    adapter = adapter_cls(store_cfg)
                self._adapters[store_id] = adapter
                logger.info("Discovered and enabled adapter: %s", store_id)
            except Exception:
                logger.exception("Failed to instantiate adapter for '%s'", store_id)

        # Custom stores
        for cs_cfg in get_enabled_custom_stores(self._config):
            try:
                adapter = CustomStoreAdapter(cs_cfg)
                self._custom_adapters[adapter.store_id] = adapter
                logger.info("Discovered and enabled custom adapter: %s", adapter.store_id)
            except Exception:
                logger.exception("Failed to instantiate custom adapter: %s", cs_cfg.get("name"))

        total = len(self._adapters) + len(self._custom_adapters)
        logger.info("StoreRegistry: %d adapters discovered (%d built-in, %d custom)",
                     total, len(self._adapters), len(self._custom_adapters))
        return total

    @property
    def adapters(self) -> Dict[str, StoreAdapter]:
        return dict(self._adapters)

    @property
    def custom_adapters(self) -> Dict[str, CustomStoreAdapter]:
        return dict(self._custom_adapters)

    @property
    def all_adapters(self) -> Dict[str, StoreAdapter]:
        """Return both built-in and custom adapters in a single dict."""
        combined = dict(self._adapters)
        combined.update(self._custom_adapters)
        return combined

    def get(self, store_id: str) -> Optional[StoreAdapter]:
        """Get an adapter by its store ID."""
        return self._adapters.get(store_id) or self._custom_adapters.get(store_id)

    def search_all(self, query: str, limit: int = 10) -> Dict[str, list]:
        """Search products across all enabled stores.

        Returns a dict of ``{store_id: [Product, ...]}``.
        """
        results: Dict[str, list] = {}
        for store_id, adapter in self.all_adapters.items():
            try:
                products = adapter.search_products(query, limit=limit)
                results[store_id] = products
                logger.debug("[%s] Found %d results for '%s'", store_id, len(products), query)
            except Exception:
                logger.exception("[%s] Search failed for '%s'", store_id, query)
                results[store_id] = []
        return results

    def close_all(self) -> None:
        """Close all adapters."""
        for adapter in self.all_adapters.values():
            try:
                if hasattr(adapter, "close"):
                    adapter.close()
            except Exception:
                logger.exception("Error closing adapter '%s'", adapter.store_id)
