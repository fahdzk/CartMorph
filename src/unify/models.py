"""
CartMorph — Unified data models.

These models represent grocery data in a store-agnostic format.
All store adapters convert their responses into these types.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime


@dataclass
class Product:
    """A single grocery product, normalized across all stores."""
    name: str
    price: Optional[float] = None
    currency: str = "USD"
    sku: Optional[str] = None
    upc: Optional[str] = None
    brand: Optional[str] = None
    category: Optional[str] = None
    image_url: Optional[str] = None
    store_id: str = ""          # which store this came from
    store_name: str = ""        # human-readable store name
    raw: Optional[dict] = field(default=None, repr=False)  # original API response

    def __str__(self) -> str:
        price_str = f"${self.price:.2f}" if self.price else "price N/A"
        return f"{self.name}  ({price_str})  [{self.store_name}]"


@dataclass
class CartItem:
    """A single item in a shopping cart."""
    product: Product
    quantity: int = 1

    @property
    def total_price(self) -> Optional[float]:
        if self.product.price is not None:
            return self.product.price * self.quantity
        return None


@dataclass
class Cart:
    """A shopping cart for a specific store."""
    store_id: str
    store_name: str
    items: List[CartItem] = field(default_factory=list)
    cart_url: Optional[str] = None  # URL to the store's cart/checkout page

    @property
    def total(self) -> Optional[float]:
        total = 0.0
        for item in self.items:
            if item.total_price is None:
                return None  # if any item has unknown price, total is unknown
            total += item.total_price
        return total

    @property
    def item_count(self) -> int:
        return sum(item.quantity for item in self.items)

    def add_item(self, product: Product, quantity: int = 1) -> None:
        # Check if product already in cart
        for item in self.items:
            if item.product.sku == product.sku:
                item.quantity += quantity
                return
        self.items.append(CartItem(product=product, quantity=quantity))


@dataclass
class StoreInfo:
    """Metadata about a configured store."""
    store_id: str
    name: str
    base_url: str
    auth_type: str
    enabled: bool
    rate_limit: Optional[str] = None
    portal_url: Optional[str] = None
    notes: Optional[str] = None
