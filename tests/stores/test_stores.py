"""Tests for the Kroger store adapter."""

import pytest
from unittest.mock import MagicMock, patch

from src.stores.kroger import KrogerAdapter
from src.utils.http_client import HttpClient


class TestKrogerAdapter:
    def test_store_metadata(self):
        config = {
            "enabled": True,
            "client_id": "test",
            "client_secret": "test",
            "base_url": "https://api.kroger.com/v1",
            "auth_url": "https://api.kroger.com/v1/connect/oauth2/token",
            "auth_type": "oauth2",
        }
        adapter = KrogerAdapter(config)
        assert adapter.store_id == "kroger"
        assert adapter.store_name == "Kroger"
        assert adapter.is_enabled is True
        assert adapter.info.auth_type == "oauth2"

    def test_disabled_store_skips_search(self):
        config = {
            "enabled": False,
            "client_id": "test",
            "client_secret": "test",
            "base_url": "https://api.kroger.com/v1",
        }
        adapter = KrogerAdapter(config)
        result = adapter.search_products("milk")
        assert result == []

    def test_search_products_mocked(self, kroger_product_response):
        config = {
            "enabled": True,
            "client_id": "test",
            "client_secret": "test",
            "base_url": "https://api.kroger.com/v1",
            "auth_url": "https://api.kroger.com/v1/connect/oauth2/token",
        }
        adapter = KrogerAdapter(config)

        mock_resp = MagicMock()
        mock_resp.json.return_value = kroger_product_response

        with patch.object(adapter, "_get_headers", return_value={}):
            adapter._http = HttpClient(base_url=config["base_url"], headers={})
            with patch.object(adapter._http, "get", return_value=mock_resp):
                products = adapter.search_products("milk", limit=5)

        assert len(products) == 2
        assert products[0].name == "Kroger Brand Whole Milk Gallon - 128 Fl Oz"
        assert products[0].price == 3.99

    def test_no_credentials_warning(self, caplog):
        import logging
        config = {
            "enabled": True,
            "base_url": "https://api.kroger.com/v1",
        }
        adapter = KrogerAdapter(config)
        assert adapter._client_credentials_auth is None

    def test_custom_location_id(self):
        config = {
            "enabled": True,
            "client_id": "test",
            "client_secret": "test",
            "base_url": "https://api.kroger.com/v1",
            "auth_url": "https://api.kroger.com/v1/connect/oauth2/token",
            "location_id": "01400456",
        }
        adapter = KrogerAdapter(config)
        assert adapter._config.get("location_id") == "01400456"
