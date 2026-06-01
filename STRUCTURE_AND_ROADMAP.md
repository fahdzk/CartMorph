# CartMorph — Project Structure and Roadmap

This file is for contributors and maintainers. It outlines the planned code
structure once development begins.

## Planned Directory Layout

```
CartMorph/
├── cartmorph.config.yaml          # Local secrets (gitignored)
├── cartmorph.config.example.yaml  # Template for new contributors
├── cartmorph.config.example.json  # JSON alternative template
├── .gitignore
├── LICENSE
├── README.md
├── CONTRIBUTING.md
├── API_REFERENCE.md
├── CHANGELOG.md
├── docs/
│   └── architecture.md            # System design decisions
├── src/
│   ├── __init__.py
│   ├── config_loader.py           # Load & validate cartmorph.config.yaml
│   ├── auth/
│   │   ├── __init__.py
│   │   ├── oauth2.py              # OAuth 2.0 client credentials + auth code
│   │   ├── api_key.py             # API key / bearer-token auth
│   │   └── token_store.py         # Token caching, expiry, refresh logic
│   ├── stores/
│   │   ├── __init__.py            # Store registry
│   │   ├── base.py                # Abstract base class for store adapters
│   │   ├── kroger.py             # Kroger API adapter
│   │   ├── walmart.py            # Walmart API adapter
│   │   ├── instacart.py          # Instacart Developer Platform adapter
│   │   ├── target.py             # Target RedSky adapter (unofficial)
│   │   └── custom.py             # Generic adapter for custom_stores entries
│   ├── unify/
│   │   ├── __init__.py
│   │   ├── models.py              # Unified Product, Cart, Store models
│   │   └── mapper.py              # Maps store-specific responses to unified models
│   └── utils/
│       ├── __init__.py
│       ├── rate_limiter.py         # Per-store rate-limit enforcement
│       └── http_client.py          # Shared HTTP client with retry + backoff
├── tests/
│   ├── __init__.py
│   ├── conftest.py                # Fixtures, hermetic test env
│   ├── test_config_loader.py
│   ├── auth/
│   │   ├── test_oauth2.py
│   │   └── test_api_key.py
│   ├── stores/
│   │   ├── test_kroger.py
│   │   ├── test_walmart.py
│   │   ├── test_instacart.py
│   │   └── test_target.py
│   └── unify/
│       └── test_mapper.py
├── scripts/
│   └── run_tests.sh
└── requirements.txt
```

## Roadmap

### Phase 0 — Foundation (config + docs)
- [x] Repository structure and .gitignore
- [x] Config schema (YAML + JSON)
- [x] Example config with all 4 stores
- [x] README, LICENSE, CONTRIBUTING, API_REFERENCE
- [ ] Validation script for ``cartmorph.config.yaml``

### Phase 1 — Auth Layer
- [ ] Token store with expiry tracking
- [ ] OAuth 2.0 client credentials flow
- [ ] OAuth 2.0 authorization code flow
- [ ] API key / bearer-token wrapper

### Phase 2 — Store Adapters
- [ ] Kroger adapter (product search, cart)
- [ ] Walmart adapter (product search)
- [ ] Instacart adapter (product search via Developer Platform)
- [ ] Target RedSky adapter (product data, unofficial)

### Phase 3 — Unified Models
- [ ] ``Product`` model (name, price, image, store, store_sku)
- [ ] ``Cart`` model (items, totals, store)
- [ ] ``Store`` metadata model

### Phase 4 — Rate Limiting & Reliability
- [ ] Per-store rate limiter
- [ ] Exponential backoff on 429 responses
- [ ] Circuit breaker pattern for failing stores

### Phase 5 — CLI / Web Interface
- [ ] CLI for searching products across all stores
- [ ] Web dashboard (optional)

### Phase 6 — Community Contributions
- [ ] Community store adapters
- [ ] Plugin system for third-party adapters
