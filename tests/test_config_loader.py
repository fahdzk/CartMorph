"""Tests for the config loader."""

import pytest
import yaml
from pathlib import Path

from src.config_loader import load_config, ConfigError, get_enabled_stores, get_enabled_custom_stores


class TestLoadConfig:
    def test_loads_yaml(self, config_yaml_path):
        config = load_config(config_yaml_path)
        assert "stores" in config
        assert "kroger" in config["stores"]

    def test_loads_json(self, tmp_path, sample_config):
        import json
        config_file = tmp_path / "cartmorph.config.json"
        with open(config_file, "w") as f:
            json.dump(sample_config, f)
        config = load_config(str(config_file))
        assert "stores" in config

    def test_missing_file(self, tmp_path):
        with pytest.raises(ConfigError, match="Config file not found"):
            load_config(str(tmp_path / "nonexistent.yaml"))

    def test_invalid_root_type(self, tmp_path):
        config_file = tmp_path / "cartmorph.config.yaml"
        with open(config_file, "w") as f:
            f.write("- not a mapping\n")
        with pytest.raises(ConfigError, match="must be a mapping"):
            load_config(str(config_file))

    def test_missing_stores_key(self, tmp_path):
        config_file = tmp_path / "cartmorph.config.yaml"
        with open(config_file, "w") as f:
            yaml.dump({"custom_stores": []}, f)
        with pytest.raises(ConfigError, match="Missing top-level key: 'stores'"):
            load_config(str(config_file))

    def test_missing_required_store_field(self, tmp_path):
        config_file = tmp_path / "cartmorph.config.yaml"
        with open(config_file, "w") as f:
            yaml.dump({
                "stores": {"badstore": {"enabled": True}},  # missing base_url
                "custom_stores": [],
            }, f)
        with pytest.raises(ConfigError, match="missing required fields"):
            load_config(str(config_file))

    def test_invalid_enabled_type(self, tmp_path):
        config_file = tmp_path / "cartmorph.config.yaml"
        with open(config_file, "w") as f:
            yaml.dump({
                "stores": {"badstore": {"enabled": "yes", "base_url": "https://x.com"}},
                "custom_stores": [],
            }, f)
        with pytest.raises(ConfigError, match="'enabled' must be true or false"):
            load_config(str(config_file))


class TestGetEnabledStores:
    def test_returns_only_enabled(self, sample_config):
        enabled = get_enabled_stores(sample_config)
        assert "kroger" in enabled
        assert "walmart" in enabled
        assert "instacart" in enabled
        assert "target" not in enabled  # disabled

    def test_all_disabled(self):
        config = {
            "stores": {
                "kroger": {"enabled": False, "base_url": "https://x.com"},
            },
            "custom_stores": [],
        }
        assert get_enabled_stores(config) == {}


class TestGetEnabledCustomStores:
    def test_returns_only_enabled(self, sample_config):
        enabled = get_enabled_custom_stores(sample_config)
        assert len(enabled) == 1
        assert enabled[0]["name"] == "TestCo"

    def test_empty_list(self):
        config = {"custom_stores": []}
        assert get_enabled_custom_stores(config) == []


class TestCustomStoreValidation:
    def test_custom_store_missing_name(self, tmp_path):
        config_file = tmp_path / "cartmorph.config.yaml"
        with open(config_file, "w") as f:
            yaml.dump({
                "stores": {},
                "custom_stores": [{"enabled": True, "base_url": "https://x.com", "auth_type": "api_key"}],
            }, f)
        with pytest.raises(ConfigError, match="missing required field 'name'"):
            load_config(str(config_file))

    def test_custom_store_missing_auth_type(self, tmp_path):
        config_file = tmp_path / "cartmorph.config.yaml"
        with open(config_file, "w") as f:
            yaml.dump({
                "stores": {},
                "custom_stores": [{"name": "BadStore", "enabled": True, "base_url": "https://x.com"}],
            }, f)
        with pytest.raises(ConfigError, match="missing required field 'auth_type'"):
            load_config(str(config_file))

    def test_custom_store_invalid_auth_type(self, tmp_path):
        config_file = tmp_path / "cartmorph.config.yaml"
        with open(config_file, "w") as f:
            yaml.dump({
                "stores": {},
                "custom_stores": [{"name": "BadStore", "enabled": True, "base_url": "https://x.com", "auth_type": "magic_link"}],
            }, f)
        with pytest.raises(ConfigError, match="invalid auth_type"):
            load_config(str(config_file))
