# API Reference — CartMorph

This document describes the authentication flow and configuration schema for
each supported grocery-chain integration.

## Configuration Schema

The configuration file (``cartmorph.config.yaml`` or ``cartmorph.config.json``)
has one top-level key:

```yaml
stores:
  <store_name>:
    enabled: true | false
    # ... store-specific keys (see per-store sections)

custom_stores: []
```

### Top-Level Fields

| Field | Type | Required | Description |
|---|---|---|---|
| ``stores`` | Map | ✅ | Map of store-name to store config block. |
| ``custom_stores`` | List | ✅ (empty list OK) | Additional unofficial or partner integrations. |

### Common Store Block Fields

Every store block under ``stores:`` shares these common fields:

| Field | Type | Required | Description |
|---|---|---|---|
| ``enabled`` | Bool | ✅ | Toggle the integration on or off. |
| ``base_url`` | String | ✅ | Root URL for all API calls. |
| ``auth_url`` | String | Conditional | OAuth 2.0 token endpoint (required for OAuth stores). |
| ``portal_url`` | String | Optional | Link to the developer portal (for reference). |
| ``notes`` | String | Optional | Free-text notes (warning, caveats, etc.). |

### OAuth 2.0 Store Fields

For stores using OAuth 2.0 (Kroger, Walmart):

| Field | Type | Required | Description |
|---|---|---|---|
| ``client_id`` | String | ✅ | OAuth client identifier. |
| ``client_secret`` | String | ✅ | OAuth client secret. |
| ``redirect_uri`` | String | Conditional | Callback URL (required for Authorization Code flow). |
| ``scopes`` | List[String] | Conditional | OAuth scopes to request. |

### API-Key Store Fields

For stores using a simple API key (Instacart):

| Field | Type | Required | Description |
|---|---|---|---|
| ``api_key`` | String | ✅ | The API key or bearer token. |
| ``dev_base_url`` | String | Optional | Development / sandbox base URL. |

### Custom Store Fields

Custom stores (in the ``custom_stores:`` array) support all of the above, plus:

| Field | Type | Required | Description |
|---|---|---|---|
| ``name`` | String | ✅ | Display name for the store. |
| ``auth_type`` | String | ✅ | One of: ``api_key``, ``bearer``, ``oauth2``, ``basic``, ``none``. |
| ``custom_headers`` | Map | Optional | Arbitrary HTTP headers sent with every request. |
| ``rate_limit`` | Map | Optional | Rate-limit configuration (``requests_per_second`` or ``requests_per_minute``). |

## Authentication Flows

### OAuth 2.0 — Client Credentials (Walmart, Instacart Connect)

Used when the application acts on its own behalf, not on behalf of an end user.

::

    POST https://auth-server.example.com/oauth/token
    Content-Type: application/x-www-form-urlencoded

    grant_type=client_credentials
    &client_id=YOUR_CLIENT_ID
    &client_secret=YOUR_CLIENT_SECRET

Response:

```json
{
  "access_token": "eyJ...",
  "token_type": "Bearer",
  "expires_in": 900
}
```

The ``access_token`` is sent as:

::

    Authorization: Bearer eyJ...

### OAuth 2.0 — Authorization Code (Kroger, user-facing flows)

Used when acting on behalf of an end user (e.g., adding items to a personal
Kroger cart).

1. **Direct the user to the authorization URL**::

       GET https://api.kroger.com/v1/connect/oauth2/authorize
         ?response_type=code
         &client_id=YOUR_CLIENT_ID
         &redirect_uri=http://localhost:3000/auth/kroger/callback
         &scope=cart.basic:write

2. **User authorizes and is redirected** to ``redirect_uri`` with a ``code``
   query parameter.

3. **Exchange the code for a token**::

       POST https://api.kroger.com/v1/connect/oauth2/token
       Content-Type: application/x-www-form-urlencoded

       grant_type=authorization_code
       &code=AUTH_CODE
       &redirect_uri=http://localhost:3000/auth/kroger/callback

### API Key (Instacart Developer Platform)

The API key is sent as a Bearer token on every request:

::

    GET /api/v1/endpoint HTTP/1.1
    Host: connect.instacart.com
    Authorization: Bearer YOUR_INSTACART_API_KEY

### No Authentication (Target RedSky)

Public endpoints require no credentials:

::

    GET /redsky_aggregations/v1/web/pdp_v1?key=store-key&tcin=12345
    Host: redsky.target.com

## Token Expiry Reference

| Store | Token Lifetime | Refresh Strategy |
|---|---|---|
| Kroger | 30 minutes | Re-request via Client Credentials or Authorization Code flow |
| Walmart | 15 minutes | Re-request via Client Credentials flow |
| Instacart (Developer Platform) | N/A (static API key) | Key does not expire; rotate manually |
| Instacart Connect | 24 hours | Re-request via Client Credentials flow |
| Target (RedSky) | N/A | No authentication token |

## Rate Limit Guidelines

| Store | Recommended Limit |
|---|---|
| Kroger | Check response headers for ``Retry-After`` |
| Walmart | 5 requests/second (Marketplace); check docs for grocery endpoints |
| Instacart | Check response headers; 429 responses include ``Retry-After`` |
| Target (RedSky) | No published limits; stay conservative (<= 5 req/sec) |

Always respect ``429 Too Many Requests`` responses and ``Retry-After``
headers. Implementing exponential backoff is recommended.
