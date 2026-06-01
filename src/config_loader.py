"""
CartMorph — Config loader and validator.

Loads ``cartmorph.config.yaml`` (or ``cartmorph.config.json``),
validates required fields, and returns a structured dict.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

try:
    import json
except ImportError:
    json = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)

REQUIRED_STORE_FIELDS = {"enabled", "base_url"}
OAUTH2_FIELDS = {"client_id", "client_secret"}
API_KEY_FIELDS = {"api_key"}
VALID_AUTH_TYPES = {"api_key", "bearer", "oauth2", "basic", "none"}


class ConfigError(Exception):
    """Raised when the configuration file is missing or invalid."""
    pass


def load_config(path: Optional[str] = None) -> Dict[str, Any]:
    """Load and validate the CartMorph configuration file.

    Args:
        path: Absolute or relative path to the config file.
              If ``None``, searches the current working directory
              for ``cartmorph.config.yaml`` then ``cartmorph.config.json``.

    Returns:
        The parsed and validated config dict.

    Raises:
        ConfigError: If the file is not found or is invalid.
    """
    config_path = _resolve_config_path(path)

    logger.info("Loading config from %s", config_path)

    with open(config_path, "r", encoding="utf-8") as f:
        if config_path.suffix == ".json":
            raw = json.load(f)
        else:
            raw = yaml.safe_load(f)

    if not isinstance(raw, dict):
        raise ConfigError(f"Config root must be a mapping, got {type(raw).__name__}")

    # Validate top-level keys
    if "stores" not in raw:
        raise ConfigError("Missing top-level key: 'stores'")

    if not isinstance(raw["stores"], dict):
        raise ConfigError("'stores' must be a mapping of store names to config blocks")

    # Validate each store block
    for store_name, store_cfg in raw["stores"].items():
        _validate_store(store_name, store_cfg)

    # Validate custom_stores
    custom_stores = raw.get("custom_stores", [])
    if not isinstance(custom_stores, list):
        raise ConfigError("'custom_stores' must be a list")
    for i, cs in enumerate(custom_stores):
        _validate_custom_store(i, cs)

    return raw


def _resolve_config_path(path: Optional[str]) -> Path:
    if path:
        p = Path(path)
        if not p.is_file():
            raise ConfigError(f"Config file not found: {path}")
        return p

    cwd = Path.cwd()
    for candidate in [
        cwd / "cartmorph.config.yaml",
        cwd / "cartmorph.config.json",
    ]:
        if candidate.is_file():
            return candidate

    raise ConfigError(
        "No config file found. Create cartmorph.config.yaml "
        "(see cartmorph.config.example.yaml)."
    )


def _validate_store(name: str, cfg: Any) -> None:
    if not isinstance(cfg, dict):
        raise ConfigError(f"Store '{name}': config block must be a mapping, got {type(cfg).__name__}")

    missing = REQUIRED_STORE_FIELDS - cfg.keys()
    if missing:
        raise ConfigError(f"Store '{name}': missing required fields: {missing}")

    if not isinstance(cfg.get("enabled"), bool):
        raise ConfigError(f"Store '{name}': 'enabled' must be true or false")


def _validate_custom_store(index: int, cfg: Any) -> None:
    if not isinstance(cfg, dict):
        raise ConfigError(f"Custom store [{index}]: must be a mapping")

    if "name" not in cfg:
        raise ConfigError(f"Custom store [{index}]: missing required field 'name'")

    auth_type = cfg.get("auth_type")
    if not auth_type:
        raise ConfigError(f"Custom store [{index}] ('{cfg.get('name')}'): missing required field 'auth_type'")

    if auth_type not in VALID_AUTH_TYPES:
        raise ConfigError(
            f"Custom store [{index}] ('{cfg.get('name')}'): "
            f"invalid auth_type '{auth_type}'. Must be one of: {VALID_AUTH_TYPES}"
        )

    if auth_type == "oauth2":
        for field in ("client_id", "client_secret", "auth_url"):
            if not cfg.get(field):
                raise ConfigError(
                    f"Custom store [{index}] ('{cfg.get('name')}'): "
                    f"auth_type 'oauth2' requires '{field}'"
                )


def get_enabled_stores(config: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """Return only the stores that have ``enabled: True``."""
    stores = config.get("stores", {})
    return {name: cfg for name, cfg in stores.items() if cfg.get("enabled") is True}


def get_enabled_custom_stores(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Return only the custom stores that have ``enabled: True``."""
    return [cs for cs in config.get("custom_stores", []) if cs.get("enabled") is True]
