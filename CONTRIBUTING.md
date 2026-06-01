# Contributing to CartMorph

First off, thank you for your interest in contributing. This document explains
how to add a new grocery-chain integration, report issues, and submit changes.

## Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [How to Add a New Integration](#how-to-add-a-new-integration)
3. [Auth Types](#auth-types)
4. [Security Rules](#security-rules)
5. [Development Workflow](#development-workflow)
6. [License](#license)

---

## Code of Conduct

All contributors are expected to engage respectfully. Harassment, abuse, or
conduct that would be unacceptable in a professional workplace is not tolerated
in any project space. Maintainers reserve the right to remove, edit, or reject
contributions that violate this standard.

## How to Add a New Integration

To add support for a new grocery chain or delivery service, follow these steps
exactly.

### Step 1 — Verify the API

Confirm the store has a public or partner developer API with documented
endpoints. If it only has an internal or undocumented API, use the
"Custom / Manual Store Integration" pattern (see below) and include any known
terms-of-service considerations.

### Step 2 — Add a Config Block to the Example File

Add a new named block under ``stores:`` (or ``custom_stores:`` for unofficial
APIs) in ``cartmorph.config.example.yaml``. Use placeholder values such as
``"YOUR_EXAMPLE_CLIENT_ID"``. Do *not* add anything to the real
``cartmorph.config.yaml`` — that file is gitignored and local-only.

### Step 3 — Document the Integration in This File

Add a section to this ``CONTRIBUTING.md`` under the
[Supported Grocery Chain APIs](#supported-grocery-chain-apis) heading below,
containing:

* A metadata table: auth type, base URL, portal link, token TTL
* Step-by-step key acquisition instructions
* A copy-paste-ready YAML config block with placeholder values

### Step 4 — Open a Pull Request

Open a pull request with your changes. In your PR description, include:

* A link to the official developer portal
* Any relevant terms-of-service notes
* Whether the integration is official or unofficial

---

## Supported Grocery Chain APIs

### Kroger

| Field | Value |
|---|---|
| **Developer Portal** | https://developer.kroger.com |
| **Auth Type** | OAuth 2.0 (Client Credentials + Authorization Code) |
| **Credentials Needed** | ``client_id``, ``client_secret`` |
| **Token Endpoint** | ``https://api.kroger.com/v1/connect/oauth2/token`` |
| **Base API URL** | ``https://api.kroger.com/v1`` |
| **Token Expiry** | 30 minutes |

#### How to Obtain Keys

1. Visit https://developer.kroger.com and create a developer account.
2. Register a new application under your developer dashboard.
3. Set your ``redirect_uri`` — for local development,
   ``http://localhost:3000/auth/kroger/callback`` is typical.
4. Copy your ``CLIENT_ID`` and ``CLIENT_SECRET`` into
   ``cartmorph.config.yaml``.

#### Available Scopes

| Scope | Description |
|---|---|
| ``product.compact`` | Read product data (name, price, images) |
| ``cart.basic:write`` | Add items to a Kroger cart |
| ``profile.compact`` | Read basic profile info |

#### Brands Covered

The Kroger API covers all Kroger Family of Stores banners, including: Kroger,
Fred Meyer, King Soopers, Ralph's, Mariano's, Smith's, Fry's, Harris Teeter,
City Market, QFC, Baker's, and Dillons.

#### Config Block

```yaml
kroger:
  enabled: true
  client_id: "YOUR_KROGER_CLIENT_ID"
  client_secret: "YOUR_KROGER_CLIENT_SECRET"
  redirect_uri: "http://localhost:3000/auth/kroger/callback"
  scopes:
    - "product.compact"
    - "cart.basic:write"
  base_url: "https://api.kroger.com/v1"
  auth_url: "https://api.kroger.com/v1/connect/oauth2/token"
```

---

### Walmart

| Field | Value |
|---|---|
| **Developer Portal** | https://developer.walmart.com |
| **Auth Type** | OAuth 2.0 (Client Credentials) |
| **Credentials Needed** | ``client_id``, ``client_secret`` |
| **Token Endpoint** | ``https://marketplace.walmartapis.com/v3/token`` |
| **Base API URL** | ``https://marketplace.walmartapis.com/v3`` |
| **Token Expiry** | 15 minutes |

#### How to Obtain Keys

1. Visit https://developer.walmart.com and register as a seller or solution
   provider.
2. Navigate to **Generate API Keys** in the Developer Portal dashboard.
3. Copy your ``Client ID`` and ``Client Secret``. Only Admin users can generate
   keys. If you regenerate, existing keys are invalidated.

> **Note:** Walmart Marketplace APIs are primarily for sellers. For grocery
> product browsing and cart, review https://walmart.io for the Recipes &
> Bundle APIs and Add-to-Cart proxy.

#### Config Block

```yaml
walmart:
  enabled: true
  client_id: "YOUR_WALMART_CLIENT_ID"
  client_secret: "YOUR_WALMART_CLIENT_SECRET"
  base_url: "https://marketplace.walmartapis.com/v3"
  auth_url: "https://marketplace.walmartapis.com/v3/token"
  token_ttl_minutes: 15
```

---

### Instacart Developer Platform

| Field | Value |
|---|---|
| **Developer Portal** | https://docs.instacart.com/developer_platform_api |
| **Auth Type** | API Key (Bearer Token) for public endpoints; OAuth 2.0 (Client Credentials) for Connect APIs |
| **Credentials Needed** | ``api_key`` (Developer Platform) or ``client_id`` + ``client_secret`` (Connect) |
| **Dev Base URL** | ``https://connect.dev.instacart.tools`` |
| **Prod Base URL** | ``https://connect.instacart.com`` |
| **Token Expiry** | 24 hours (Connect OAuth tokens) |

#### How to Obtain Keys

**Developer Platform (public API key):**
1. Visit https://docs.instacart.com/developer_platform_api and apply for access.
2. Log into the **Instacart Developer Dashboard**.
3. Navigate to **API Keys -> Create New API Key**.
4. Choose ``Development`` or ``Production``, give it a name, and generate.
5. Copy the key immediately — it cannot be viewed again.

**Connect APIs (retailer partners only):**
Contact an Instacart representative directly for ``client_id`` and
``client_secret``.

#### Coverage

Instacart's network covers 85,000+ stores across 1,500+ retail banners,
including Publix, ALDI, Costco, Kroger, Wegmans, Sprouts, and many regional
chains.

#### Config Block

```yaml
instacart:
  enabled: true
  api_key: "YOUR_INSTACART_API_KEY"
  # For Connect API (retailer partners only):
  # client_id: "YOUR_INSTACART_CLIENT_ID"
  # client_secret: "YOUR_INSTACART_CLIENT_SECRET"
  base_url: "https://connect.instacart.com"
  dev_base_url: "https://connect.dev.instacart.tools"
  token_ttl_hours: 24
```

---

### Target (RedSky)

| Field | Value |
|---|---|
| **Official Developer Portal** | https://developer.target.com |
| **Auth Type** | None required for public product endpoints |
| **Base URL** | ``https://redsky.target.com`` |
| **Status** | Unofficial / semi-public |

⚠️ **Important:** Target does not maintain an official public developer API for
third-party grocery integrations. Use responsibly and respect rate limits.

#### Config Block

```yaml
target:
  enabled: false
  base_url: "https://redsky.target.com"
  notes: >
    No official API key required for public product endpoints.
    Enable only after reviewing Target's current terms of service.
```

---

## Custom / Manual Store Integration

Use this pattern for any store that does not have a formal developer program but
exposes an HTTP API.

### Required Fields

| Field | Required | Description |
|---|---|---|
| ``name`` | ✅ | Display name (e.g. "H-E-B") |
| ``api_key`` | Conditional | API key credential (if applicable) |
| ``base_url`` | ✅ | Root endpoint for API calls |
| ``auth_type`` | ✅ | One of: ``api_key``, ``oauth2``, ``bearer``, ``basic``, ``none`` |
| ``client_id`` | Conditional | Required if ``auth_type`` is ``oauth2`` |
| ``client_secret`` | Conditional | Required if ``auth_type`` is ``oauth2`` |
| ``auth_url`` | Conditional | Token endpoint for OAuth 2.0 flows |
| ``custom_headers`` | Optional | Extra request headers |
| ``rate_limit`` | Optional | Requests per second/minute ceiling |
| ``notes`` | Optional | Human-readable notes |

### Example

```yaml
custom_stores:
  - name: "H-E-B"
    enabled: true
    api_key: "YOUR_HEB_API_KEY"
    base_url: "https://api.heb.com/v1"
    auth_type: "api_key"
    custom_headers:
      x-api-version: "2024-01"
    rate_limit:
      requests_per_minute: 60
    notes: "H-E-B partner API — requires prior partnership agreement."
```

---

## Auth Type Reference

| Value | Description | Required Fields |
|---|---|---|
| ``api_key`` | Key sent as query param or header | ``api_key`` |
| ``bearer`` | ``Authorization: Bearer <token>`` header | ``api_key`` (used as token) |
| ``oauth2`` | Client Credentials or Auth Code flow | ``client_id``, ``client_secret``, ``auth_url`` |
| ``basic`` | HTTP Basic Auth (``username:password``) | ``client_id`` (username), ``client_secret`` (password) |
| ``none`` | No authentication required | — |

---

## Security Rules

1. **Never commit credentials.** ``cartmorph.config.yaml`` is gitignored. Do not
   remove it from ``.gitignore``.
2. **Use the example file as a template.** Copy
   ``cartmorph.config.example.yaml`` to ``cartmorph.config.yaml`` and fill in
   your values.
3. **Rotate keys immediately if exposed.** Use ``git filter-repo`` or BFG Repo
   Cleaner to purge from history.
4. **Use environment-specific keys** where providers allow.
5. **Respect rate limits** — abuse gets keys revoked.
6. **Limit OAuth scopes** to only what your integration needs.
7. **Each developer uses their own keys** — do not share.

---

## Development Workflow

1. Fork the repository.
2. Create a feature branch: ``git checkout -b feat/my-integration``.
3. Make your changes (config example + documentation).
4. Test that your config block validates (if a validator exists).
5. Open a pull request against ``main``.
6. Respond to review comments and iterate.

---

## License

By contributing to CartMorph, you agree that your contributions will be
licensed under the BSD 3-Clause License. See ``LICENSE`` for the full text.
