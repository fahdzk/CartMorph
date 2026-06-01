"""
CartMorph — Mapper from store-specific API responses to unified models.

Each store adapter produces raw dict responses; this module converts
them into ``Product`` instances with consistent field names.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from ..unify.models import Product

logger = logging.getLogger(__name__)


def map_kroger_product(raw: Dict[str, Any]) -> Product:
    """Map a single Kroger API product item to a unified ``Product``."""
    item_id = raw.get("itemId", "")
    desc = raw.get("description", "Unknown Product")

    # Price parsing — Kroger returns price dicts inside items
    price = None
    items_list = raw.get("items", [])
    if items_list:
        price_info = items_list[0].get("price", {})
        regular = price_info.get("regular")
        if regular is not None:
            try:
                price = float(regular)
            except (TypeError, ValueError):
                pass

    # Images
    images = raw.get("images", [])
    image_url = None
    for img in images:
        for size in img.get("sizes", []):
            if size.get("size") == "large":
                image_url = size.get("url")
                break
        if image_url:
            break

    brand = raw.get("brand", "")
    upc = raw.get("upc", "")

    return Product(
        name=desc,
        price=price,
        sku=item_id,
        upc=upc,
        brand=brand,
        image_url=image_url,
        store_id="kroger",
        store_name="Kroger",
        raw=raw,
    )


def map_kroger_products(raw_list: List[Dict[str, Any]]) -> List[Product]:
    """Map a list of Kroger product items."""
    products = []
    for raw in raw_list:
        try:
            products.append(map_kroger_product(raw))
        except Exception:
            logger.exception("Failed to map Kroger product: %s", raw.get("itemId"))
    return products


def map_walmart_product(raw: Dict[str, Any]) -> Product:
    """Map a single Walmart API product item to a unified ``Product``."""
    name = raw.get("name", "Unknown Product")

    price = None
    price_info = raw.get("price", {})
    if isinstance(price_info, dict):
        val = price_info.get("amount") or price_info.get("currentPrice")
        if val is not None:
            try:
                price = float(val)
            except (TypeError, ValueError):
                pass
    elif isinstance(price_info, (int, float)):
        price = float(price_info)

    sku = raw.get("sku") or raw.get("itemId") or raw.get("productId")
    upc = raw.get("upc", "")
    brand = raw.get("brandName", "") or raw.get("brand", "")
    image_url = raw.get("image") or raw.get("largeImage") or raw.get("mediumImage")

    return Product(
        name=name,
        price=price,
        sku=str(sku) if sku else None,
        upc=upc,
        brand=brand,
        image_url=image_url,
        store_id="walmart",
        store_name="Walmart",
        raw=raw,
    )


def map_walmart_products(raw_list: List[Dict[str, Any]]) -> List[Product]:
    products = []
    for raw in raw_list:
        try:
            products.append(map_walmart_product(raw))
        except Exception:
            logger.exception("Failed to map Walmart product: %s", raw.get("name"))
    return products


def map_instacart_product(raw: Dict[str, Any]) -> Product:
    """Map a single Instacart API product item to a unified ``Product``."""
    name = raw.get("name", "Unknown Product")

    price = None
    price_val = raw.get("price") or raw.get("reference_price")
    if price_val is not None:
        try:
            price = float(price_val)
        except (TypeError, ValueError):
            pass

    sku = raw.get("id") or raw.get("product_id") or raw.get("retailer_id")
    upc = raw.get("upc", "")
    brand = raw.get("brand", "")
    image_url = raw.get("image_url") or raw.get("image_path")

    return Product(
        name=name,
        price=price,
        sku=str(sku) if sku else None,
        upc=upc,
        brand=brand,
        image_url=image_url,
        store_id="instacart",
        store_name="Instacart",
        raw=raw,
    )


def map_instacart_products(raw_list: List[Dict[str, Any]]) -> List[Product]:
    products = []
    for raw in raw_list:
        try:
            products.append(map_instacart_product(raw))
        except Exception:
            logger.exception("Failed to map Instacart product: %s", raw.get("name"))
    return products


def map_target_product(raw: Dict[str, Any]) -> Product:
    """Map a single Target RedSky product item to a unified ``Product``."""
    # The RedSky response has nested product data
    item = raw.get("item", raw)  # fallback to raw if no 'item' key
    product_desc = item.get("product_description", {})

    title = product_desc.get("title", "Unknown Product")

    price = None
    price_block = item.get("price", {}) or product_desc.get("price", {})
    if isinstance(price_block, dict):
        val = price_block.get("current_retail") or price_block.get("list_price")
        if val is not None:
            try:
                price = float(val)
            except (TypeError, ValueError):
                pass

    tcin = item.get("tcin") or raw.get("tcin")
    upc = item.get("upc", "")

    image_url = None
    images = item.get("enrichment", {}).get("images", {})
    if isinstance(images, dict):
        image_url = images.get("primary_image_url") or images.get("image_url")
    elif isinstance(images, list) and images:
        image_url = images[0].get("base_url")

    return Product(
        name=title,
        price=price,
        sku=tcin,
        upc=upc,
        image_url=image_url,
        store_id="target",
        store_name="Target",
        raw=raw,
    )


def map_target_products(raw_list: List[Dict[str, Any]]) -> List[Product]:
    products = []
    for raw in raw_list:
        try:
            products.append(map_target_product(raw))
        except Exception:
            logger.exception("Failed to map Target product")
    return products
