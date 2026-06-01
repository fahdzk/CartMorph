"""Tests for the auth module."""

import time
import pytest
from unittest.mock import MagicMock, patch

from src.auth.token_store import TokenEntry, TokenStore
from src.auth.api_key import ApiKeyAuth
from src.auth.oauth2 import OAuth2ClientCredentials, OAuth2AuthorizationCode


class TestTokenEntry:
    def test_is_expired_no_expiry(self):
        entry = TokenEntry(access_token="test", expires_at=0)
        assert not entry.is_expired

    def test_is_expired_past(self):
        entry = TokenEntry(access_token="test", expires_at=time.time() - 10)
        assert entry.is_expired

    def test_is_expired_future(self):
        entry = TokenEntry(access_token="test", expires_at=time.time() + 3600)
        assert not entry.is_expired

    def test_is_stale_near_expiry(self):
        entry = TokenEntry(access_token="test", expires_at=time.time() + 30)
        assert entry.is_stale  # within DEFAULT_EXPIRY_BUFFER (60s)

    def test_is_stale_far_from_expiry(self):
        entry = TokenEntry(access_token="test", expires_at=time.time() + 3600)
        assert not entry.is_stale


class TestTokenStore:
    def test_get_returns_token(self):
        store = TokenStore()
        entry = TokenEntry(access_token="my_token", expires_at=time.time() + 3600)
        store.set("test", entry)
        assert store.get("test") == "my_token"

    def test_get_no_fetcher_returns_none(self):
        store = TokenStore()
        assert store.get("nonexistent") is None

    def test_auto_refresh_on_stale(self):
        store = TokenStore()
        entry = TokenEntry(access_token="old_token", expires_at=time.time() + 30)
        store.set("test", entry)

        # Register a fetcher that returns a new token
        def fetcher():
            return TokenEntry(access_token="new_token", expires_at=time.time() + 3600)

        store.set_fetcher("test", fetcher)
        assert store.get("test") == "new_token"

    def test_invalidate(self):
        store = TokenStore()
        entry = TokenEntry(access_token="token", expires_at=time.time() + 3600)
        store.set("test", entry)
        store.invalidate("test")
        # No fetcher registered, so get returns None
        assert store.get("test") is None

    def test_clear(self):
        store = TokenStore()
        store.set("a", TokenEntry(access_token="aa", expires_at=time.time() + 3600))
        store.set("b", TokenEntry(access_token="bb", expires_at=time.time() + 3600))
        store.clear()
        assert store.get("a") is None
        assert store.get("b") is None

    def test_status(self):
        store = TokenStore()
        store.set("a", TokenEntry(access_token="aa", expires_at=time.time() + 3600))
        status = store.status()
        assert "a" in status
        assert status["a"]["has_token"] is True


class TestApiKeyAuth:
    def test_to_headers(self):
        auth = ApiKeyAuth(api_key="my-real-key-123")
        headers = auth.to_headers()
        assert headers == {"Authorization": "Bearer my-real-key-123"}

    def test_placeholder_key_not_configured(self):
        auth = ApiKeyAuth(api_key="YOUR_API_KEY")
        assert not auth.is_configured

    def test_configured_with_real_key(self):
        auth = ApiKeyAuth(api_key="abc123realkey")
        assert auth.is_configured

    def test_custom_header_format(self):
        auth = ApiKeyAuth(api_key="mykey", header_format="Token {key}")
        assert auth.to_headers() == {"Authorization": "Token mykey"}

    def test_str_configured(self):
        auth = ApiKeyAuth(api_key="abcdefghijklmnop")
        s = str(auth)
        assert "abcd" in s
        assert "mnop" in s

    def test_str_not_configured(self):
        auth = ApiKeyAuth(api_key="YOUR_KEY")
        assert str(auth) == "ApiKeyAuth(NOT_CONFIGURED)"


class TestOAuth2ClientCredentials:
    def test_to_auth_header_fetches_token(self):
        auth = OAuth2ClientCredentials(
            client_id="test_id",
            client_secret="test_secret",
            token_url="https://auth.example.com/token",
        )
        # Mock the HTTP call in fetch_token
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "access_token": "test_access_token",
            "token_type": "Bearer",
            "expires_in": 1800,
        }
        with patch("src.auth.oauth2.HttpClient") as mock_http_cls:
            mock_http = MagicMock()
            mock_http.__enter__ = MagicMock(return_value=mock_http)
            mock_http.__exit__ = MagicMock(return_value=False)
            mock_http.post.return_value = mock_resp
            mock_http_cls.return_value = mock_http

            headers = auth.to_auth_header()

        assert headers == {"Authorization": "Bearer test_access_token"}


class TestOAuth2AuthorizationCode:
    def test_get_authorization_url(self):
        auth = OAuth2AuthorizationCode(
            client_id="test_id",
            client_secret="test_secret",
            authorize_url="https://auth.example.com/authorize",
            token_url="https://auth.example.com/token",
            redirect_uri="http://localhost:3000/callback",
            scopes=["cart.basic:write"],
        )
        url = auth.get_authorization_url()
        assert "response_type=code" in url
        assert "client_id=test_id" in url
        assert "redirect_uri=http" in url
        assert "scope=cart.basic%3Awrite" in url

    def test_get_authorization_url_with_state(self):
        auth = OAuth2AuthorizationCode(
            client_id="test_id",
            client_secret="test_secret",
            authorize_url="https://auth.example.com/authorize",
            token_url="https://auth.example.com/token",
            redirect_uri="http://localhost:3000/callback",
        )
        url = auth.get_authorization_url(state="xyz123")
        assert "state=xyz123" in url

    def test_get_token_returns_none_when_not_authorized(self):
        auth = OAuth2AuthorizationCode(
            client_id="test",
            client_secret="test",
            authorize_url="https://x.com/auth",
            token_url="https://x.com/token",
            redirect_uri="http://localhost/callback",
        )
        assert auth.get_token() is None
