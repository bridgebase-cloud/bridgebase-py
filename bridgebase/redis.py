"""Redis session — sets up gateway + proxy + credentials, returns native redis-py client."""

from __future__ import annotations

import logging
from typing import Any, Optional

from bridgebase.base import BaseSession
from bridgebase.credentials import DatabaseCredentials
from bridgebase.exceptions import ConnectionError as BridgeConnectionError

logger = logging.getLogger("bridgebase.redis")


class RedisSession(BaseSession):
    """Session that returns the native ``redis.Redis`` client.

    Usage::

        session = RedisSession(region="ap-south-1", jwt_token="...", ...)
        r = session.connect()  # native redis.Redis client
        r.set("key", "value")
        r.get("key")
        session.close()

        # Or with context manager:
        with RedisSession(...) as r:
            r.set("key", "value")
    """

    _db_label = "Redis"

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(db_type="redis", **kwargs)

    # -- BaseSession hooks -------------------------------------------------

    def _connect_native(self, credentials: Optional[DatabaseCredentials], proxy_port: int) -> Any:
        try:
            import redis as _redis  # type: ignore[import-untyped]
        except ImportError as exc:
            raise BridgeConnectionError(
                "redis is required for Redis support. "
                "Install it with: pip install bridgebase[redis]"
            ) from exc

        assert credentials is not None
        try:
            client = _redis.Redis(
                host="127.0.0.1",
                port=proxy_port,
                username=credentials.username,
                password=credentials.password,
                decode_responses=True,
            )
            client.ping()
        except Exception as exc:
            raise BridgeConnectionError(f"Redis connection failed: {exc}") from exc

        return client

    def _close_native(self, native_client: Any) -> None:
        native_client.close()
