"""BridgeBase — Multi‑database SDK with gateway socket authentication.

Modular package layout:

- ``bridgebase.core`` — database-agnostic infrastructure
- ``bridgebase.redis`` — Redis/Valkey adapter
- ``bridgebase.tigerbeetle`` — TigerBeetle adapter
- ``bridgebase.mysql`` — MySQL adapter (future)
- ``bridgebase.postgres`` — PostgreSQL adapter (future)
- ``bridgebase.clickhouse`` — ClickHouse adapter (future)

Quick start::

    from bridgebase.redis import redis
    from bridgebase.tigerbeetle import tigerbeetle

    with redis(jwt_token="...") as rd:
        rd.set("key", "value")

    with tigerbeetle(jwt_token="...") as tb:
        account = tigerbeetle.Account(id=1, ledger=1, code=1)
        tb.create_accounts([account])
"""

from __future__ import annotations

__all__ = ["__version__"]

__version__ = "0.2.0"
