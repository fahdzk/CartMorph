"""
CartMorph — CLI entry point.

Usage:
    python -m cartmorph search "milk" --limit 5
    python -m cartmorph stores
    python -m cartmorph config
"""

from __future__ import annotations

import argparse
import logging
import sys
from typing import List, Optional

from . import __version__
from .config_loader import load_config, ConfigError, get_enabled_stores
from .auth import TokenStore
from .stores import StoreRegistry
from .unify.models import Product

logger = logging.getLogger("cartmorph")


def setup_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s  %(name)-20s  %(levelname)-7s  %(message)s",
        datefmt="%H:%M:%S",
    )


def print_products(products: list, store_name: str = "") -> None:
    if store_name:
        print(f"\n{'='*50}")
        print(f"  {store_name}")
        print(f"{'='*50}")
    if not products:
        print("  No results found.")
        return
    for i, p in enumerate(products, 1):
        price_str = f"${p.price:.2f}" if p.price is not None else "N/A"
        print(f"  {i:2d}. {p.name}")
        print(f"      Price: {price_str}  |  SKU: {p.sku or 'N/A'}  |  Brand: {p.brand or 'N/A'}")
    print()


def cmd_search(args: argparse.Namespace) -> int:
    try:
        config = load_config(args.config)
    except ConfigError as e:
        print(f"Config error: {e}", file=sys.stderr)
        return 1

    token_store = TokenStore()
    registry = StoreRegistry(config, token_store)
    count = registry.discover()

    if count == 0:
        print("No stores enabled. Edit cartmorph.config.yaml and set 'enabled: true' for stores you want.")
        return 1

    if args.store:
        adapter = registry.get(args.store)
        if adapter is None:
            print(f"Store '{args.store}' not found or not enabled.", file=sys.stderr)
            return 1
        products = adapter.search_products(args.query, limit=args.limit)
        print_products(products, store_name=adapter.store_name)
    else:
        results = registry.search_all(args.query, limit=args.limit)
        for store_id, products in results.items():
            adapter = registry.get(store_id)
            name = adapter.store_name if adapter else store_id
            print_products(products, store_name=name)

    registry.close_all()
    return 0


def cmd_stores(args: argparse.Namespace) -> int:
    try:
        config = load_config(args.config)
    except ConfigError as e:
        print(f"Config error: {e}", file=sys.stderr)
        return 1

    stores = config.get("stores", {})
    if not stores:
        print("No stores configured.")
        return 0

    print(f"\n{'Store':<15} {'Enabled':<10} {'Auth URL / Base URL'}")
    print("-" * 70)
    for name, cfg in stores.items():
        enabled = "yes" if cfg.get("enabled") else "no"
        url = cfg.get("auth_url") or cfg.get("base_url", "N/A")
        print(f"{name:<15} {enabled:<10} {url}")

    custom = config.get("custom_stores", [])
    if custom:
        print(f"\nCustom stores:")
        for cs in custom:
            name = cs.get("name", "?")
            enabled = "yes" if cs.get("enabled") else "no"
            auth_type = cs.get("auth_type", "none")
            print(f"  {name:<15} {enabled:<10} auth_type={auth_type}")

    print()
    return 0


def cmd_config(args: argparse.Namespace) -> int:
    try:
        config = load_config(args.config)
    except ConfigError as e:
        print(f"Config error: {e}", file=sys.stderr)
        return 1

    enabled = get_enabled_stores(config)
    print(f"\nCartMorph v{__version__}")
    print(f"Config loaded successfully.")
    print(f"Total stores configured: {len(config.get('stores', {}))}")
    print(f"Enabled stores: {len(enabled)}")
    print(f"Custom stores: {len(config.get('custom_stores', []))}")
    if enabled:
        print(f"\nEnabled: {', '.join(enabled.keys())}")
    print()
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="cartmorph",
        description="CartMorph — Unified grocery product search across multiple chains.",
    )
    parser.add_argument("--config", "-c", default=None, help="Path to cartmorph.config.yaml")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable debug logging")
    parser.add_argument("--version", action="version", version=f"CartMorph {__version__}")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # search
    search_p = subparsers.add_parser("search", help="Search products across stores")
    search_p.add_argument("query", help="Search term (e.g. 'milk', 'bread')")
    search_p.add_argument("--limit", "-l", type=int, default=10, help="Max results per store")
    search_p.add_argument("--store", "-s", default=None, help="Search a specific store only")

    # stores
    subparsers.add_parser("stores", help="List configured stores")

    # config
    subparsers.add_parser("config", help="Show config info")

    args = parser.parse_args(argv)
    setup_logging(args.verbose)

    if args.command is None:
        parser.print_help()
        return 0

    handlers = {
        "search": cmd_search,
        "stores": cmd_stores,
        "config": cmd_config,
    }
    handler = handlers.get(args.command)
    if handler:
        return handler(args)

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
