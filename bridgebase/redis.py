"""Redis / Valkey session — sets up gateway + proxy, returns native client.

The native ``redis.Redis`` client connects through the
local proxy which tunnels traffic over the gateway socket.

Compatible with both Redis and Valkey (API‑identical).
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from bridgebase.base import BaseSession
from bridgebase.credentials import DatabaseCredentials
from bridgebase.exceptions import ConnectionError as BridgeConnectionError

logger = logging.getLogger("bridgebase.redis")


class RedisSession(BaseSession):
    """Session that returns a native ``redis.Redis`` client.

    Usage::

        session = RedisSession(jwt_token="...", ...)
        rd = session.connect()   # native redis.Redis
        rd.set("key", "value")
        rd.get("key")
        session.close()

        # Or with context manager:
        with RedisSession(...) as rd:
            rd.set("key", "value")
    """

    _db_label = "Redis"

    def __init__(self, *, db: int = 0, **kwargs: Any) -> None:
        super().__init__(db_type="redis", **kwargs)
        self._redis_db = db

    # -- BaseSession hooks -------------------------------------------------

    @property
    def _requires_credentials(self) -> bool:
        return False

    def _connect_native(self, credentials: Optional[DatabaseCredentials], proxy_port: int) -> Any:
        try:
            import redis as redis_lib  # type: ignore[import-untyped]
        except ImportError as exc:
            raise BridgeConnectionError(
                "redis is required for Redis/Valkey support. "
                "Install it with: pip install bridgebase[redis]"
            ) from exc

        try:
            client = redis_lib.Redis(
                host="127.0.0.1",
                port=proxy_port,
                db=self._redis_db,
                decode_responses=True,
            )
            # Verify connection is alive.
            client.ping()
        except Exception as exc:
            raise BridgeConnectionError(f"Redis connection failed: {exc}") from exc

        return client

    def _close_native(self, native_client: Any) -> None:
        try:
            native_client.close()
        except Exception:
            pass
