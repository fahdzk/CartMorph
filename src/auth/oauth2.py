"""
CartMorph — OAuth 2.0 authentication helpers.

Supports:
- Client Credentials flow (Walmart, Instacart Connect)
- Authorization Code flow (Kroger)
"""

from __future__ import annotations

import time
import logging
from typing import Dict, List, Optional
from urllib.parse import urlencode

from ..auth.token_store import TokenEntry
from ..utils.http_client import HttpClient

logger = logging.getLogger(__name__)


class OAuth2ClientCredentials:
    """OAuth 2.0 Client Credentials flow.

    Usage::

        auth = OAuth2ClientCredentials(
            client_id="...",
            client_secret="...",
            token_url="https://...",
        )
        token = auth.get_token()
    """

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        token_url: str,
        scopes: Optional[List[str]] = None,
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.token_url = token_url
        self.scopes = scopes or []
        self._token: Optional[TokenEntry] = None

    def fetch_token(self) -> TokenEntry:
        """Request a new access token from the token endpoint."""
        data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }
        if self.scopes:
            data["scope"] = " ".join(self.scopes)

        with HttpClient() as http:
            resp = http.post(self.token_url, data=data)

        payload = resp.json()
        expires_in = payload.get("expires_in", 1800)
        entry = TokenEntry(
            access_token=payload["access_token"],
            token_type=payload.get("token_type", "Bearer"),
            expires_at=time.time() + expires_in,
            fetched_at=time.time(),
        )
        self._token = entry
        logger.debug("Fetched OAuth2 client credentials token (expires_in=%ds)", expires_in)
        return entry

    def get_token(self) -> str:
        """Return a valid access token, fetching a new one if needed."""
        if self._token and not self._token.is_stale:
            return self._token.access_token
        return self.fetch_token().access_token

    def to_auth_header(self) -> Dict[str, str]:
        """Return the ``Authorization`` header dict."""
        return {"Authorization": f"Bearer {self.get_token()}"}


class OAuth2AuthorizationCode:
    """OAuth 2.0 Authorization Code flow.

    This is a two-step flow:
    1. Call ``get_authorization_url()`` and direct the user to that URL.
    2. After the user authorizes, call ``exchange_code(auth_code)``.

    Usage::

        auth = OAuth2AuthorizationCode(
            client_id="...",
            client_secret="...",
            authorize_url="https://.../authorize",
            token_url="https://.../token",
            redirect_uri="http://localhost:3000/auth/kroger/callback",
            scopes=["cart.basic:write"],
        )
        url = auth.get_authorization_url()
        # ... user visits URL and authorizes ...
        token = auth.exchange_code("AUTH_CODE_FROM_CALLBACK")
    """

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        authorize_url: str,
        token_url: str,
        redirect_uri: str,
        scopes: Optional[List[str]] = None,
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.authorize_url = authorize_url
        self.token_url = token_url
        self.redirect_uri = redirect_uri
        self.scopes = scopes or []
        self._token: Optional[TokenEntry] = None

    def get_authorization_url(self, state: Optional[str] = None) -> str:
        """Build the authorization URL to redirect the user to."""
        params: Dict[str, str] = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
        }
        if self.scopes:
            params["scope"] = " ".join(self.scopes)
        if state:
            params["state"] = state
        return f"{self.authorize_url}?{urlencode(params)}"

    def exchange_code(self, code: str) -> TokenEntry:
        """Exchange an authorization code for an access token."""
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.redirect_uri,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }
        with HttpClient() as http:
            resp = http.post(self.token_url, data=data)

        payload = resp.json()
        expires_in = payload.get("expires_in", 1800)
        entry = TokenEntry(
            access_token=payload["access_token"],
            token_type=payload.get("token_type", "Bearer"),
            expires_at=time.time() + expires_in,
            refresh_token=payload.get("refresh_token"),
            fetched_at=time.time(),
        )
        self._token = entry
        logger.debug("Fetched OAuth2 authorization code token (expires_in=%ds)", expires_in)
        return entry

    def get_token(self) -> Optional[str]:
        """Return the current access token if available."""
        if self._token:
            if not self._token.is_expired:
                return self._token.access_token
            logger.warning("Authorization code token has expired. Re-authorization required.")
        return None

    def to_auth_header(self) -> Dict[str, str]:
        token = self.get_token()
        if not token:
            raise RuntimeError("No valid token. Complete the authorization code flow first.")
        return {"Authorization": f"Bearer {token}"}
