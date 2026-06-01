CartMorph
=========

Unified multi-chain grocery delivery integration platform. One config, multiple stores.

Supported Integrations
----------------------

| Store       | Auth Type     | Status       |
|-------------|--------------|--------------|
| Kroger      | OAuth 2.0    | Official API |
| Walmart     | OAuth 2.0    | Official API |
| Instacart   | API Key / OAuth 2.0 | Official API |
| Target      | None         | Unofficial (RedSky) |

Quick Start
-----------

1. Copy the example config::

       cp cartmorph.config.example.yaml cartmorph.config.yaml

2. Fill in your API keys. Each key is obtained from the store's developer
   portal — see the table above for portal links or check CONTRIBUTING.md
   for step-by-step instructions per provider.

3. Enable the stores you want by setting ``enabled: true`` for each block.

4. If contributing a new integration, see ``CONTRIBUTING.md``.

Security
--------

* ``cartmorph.config.yaml`` is listed in ``.gitignore`` and must **never**
  be committed.
* Use separate Development / Production keys where the provider allows.
* Rotate any key immediately if it is accidentally exposed.

License
-------

Apache 2.0. See ``LICENSE``.
