"""CartMorph — Pytest configuration and shared fixtures."""

import os
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch


@pytest.fixture(autouse=True)
def hermetic_env(monkeypatch):
    """Ensure tests run in a hermetic environment with no real credentials."""
    # Strip any real API keys
    for key in list(os.environ.keys()):
        if any(s in key for s in ["_API_KEY", "_TOKEN", "_SECRET", "_CLIENT_ID"]):
            monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("TZ", "UTC")
    monkeypatch.setenv("LANG", "C.UTF-8")
    yield


@pytest.fixture
def sample_config():
    """Return a valid sample config dict for testing."""
    return {
        "stores": {
            "kroger": {
                "enabled": True,
                "client_id": "test_kroger_id",
                "client_secret": "test_kroger_secret",
                "redirect_uri": "http://localhost:3000/auth/kroger/callback",
                "scopes": ["product.compact"],
                "base_url": "https://api.kroger.com/v1",
                "auth_url": "https://api.kroger.com/v1/connect/oauth2/token",
                "portal_url": "https://developer.kroger.com",
            },
            "walmart": {
                "enabled": True,
                "client_id": "test_walmart_id",
                "client_secret": "test_walmart_secret",
                "base_url": "https://marketplace.walmartapis.com/v3",
                "auth_url": "https://marketplace.walmartapis.com/v3/token",
                "portal_url": "https://developer.walmart.com",
            },
            "instacart": {
                "enabled": True,
                "api_key": "test_instacart_key",
                "base_url": "https://connect.instacart.com",
                "dev_base_url": "https://connect.dev.instacart.tools",
                "portal_url": "https://docs.instacart.com/developer_platform_api",
            },
            "target": {
                "enabled": False,
                "base_url": "https://redsky.target.com",
                "notes": "Unofficial API",
            },
        },
        "custom_stores": [
            {
                "name": "TestCo",
                "enabled": True,
                "api_key": "test_custom_key",
                "base_url": "https://api.testco.example.com",
                "auth_type": "api_key",
                "rate_limit": {"requests_per_minute": 60},
            }
        ],
    }


@pytest.fixture
def config_yaml_path(tmp_path, sample_config):
    """Write sample_config to a temp YAML file and return its path."""
    import yaml
    config_file = tmp_path / "cartmorph.config.yaml"
    with open(config_file, "w") as f:
        yaml.dump(sample_config, f)
    return str(config_file)


@pytest.fixture
def kroger_product_response():
    """Return a mock Kroger API product search response."""
    return {
        "data": [
            {
                "itemId": "0001111041700",
                "upc": "0001111041700",
                "description": "Kroger Brand Whole Milk Gallon - 128 Fl Oz",
                "brand": "Kroger",
                "items": [{"price": {"regular": 3.99, "promo": 3.49}}],
                "images": [
                    {"sizes": [{"size": "thumbnail", "url": "https://example.com/thumb.jpg"},
                               {"size": "large", "url": "https://example.com/large.jpg"}]}
                ],
            },
            {
                "itemId": "0001111041701",
                "upc": "0001111041701",
                "description": "Kroger Brand 2% Reduced Fat Milk Gallon",
                "brand": "Kroger",
                "items": [{"price": {"regular": 3.79}}],
                "images": [],
            },
        ]
    }


@pytest.fixture
def walmart_product_response():
    """Return a mock Walmart API product response."""
    return {
        "items": [
            {
                "name": "Great Value Whole Milk, 1 Gallon",
                "sku": "12345678",
                "upc": "007874212345",
                "brandName": "Great Value",
                "price": {"amount": 3.68, "currentPrice": 3.68},
                "image": "https://i5.walmartimages.com/milk.jpg",
            }
        ]
    }


@pytest.fixture
def instacart_product_response():
    """Return a mock Instacart API product response."""
    return {
        "products": [
            {
                "id": "abc123",
                "name": "Organic Valley Whole Milk, 64 fl oz",
                "reference_price": 4.59,
                "upc": "001234567890",
                "brand": "Organic Valley",
                "image_url": "https://instacart.com/images/milk.jpg",
            }
        ]
    }


@pytest.fixture
def target_product_response():
    """Return a mock Target RedSky product search response."""
    return {
        "search_response": {
            "items": {
                "Item": [
                    {
                        "tcin": "12345678",
                        "upc": "008523901234",
                        "item": {
                            "product_description": {
                                "title": " Horizon Organic Whole Milk Half Gallon",
                                "price": {"current_retail": 4.99},
                            },
                            "enrichment": {
                                "images": {
                                    "primary_image_url": "https://target.com/images/milk.jpg"
                                }
                            },
                        },
                    }
                ]
            }
        }
    }
