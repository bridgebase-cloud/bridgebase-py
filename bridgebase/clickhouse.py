"""ClickHouse session — sets up gateway + proxy + credentials, returns native clickhouse-driver client."""

from __future__ import annotations

import logging
from typing import Any, Optional

from bridgebase.base import BaseSession
from bridgebase.credentials import DatabaseCredentials
from bridgebase.exceptions import ConnectionError as BridgeConnectionError

logger = logging.getLogger("bridgebase.clickhouse")


class ClickHouseSession(BaseSession):
    """Session that returns the native ``clickhouse_driver.Client``.

    Usage::

        session = ClickHouseSession(region="ap-south-1", jwt_token="...", database="analytics", ...)
        ch = session.connect()  # native clickhouse_driver.Client
        ch.execute("SELECT 1")
        session.close()

        # Or with context manager:
        with ClickHouseSession(...) as ch:
            ch.execute("SELECT 1")
    """

    _db_label = "ClickHouse"

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(db_type="clickhouse", **kwargs)

    # -- BaseSession hooks -------------------------------------------------

    def _connect_native(self, credentials: Optional[DatabaseCredentials], proxy_port: int) -> Any:
        try:
            from clickhouse_driver import Client as CHClient  # type: ignore[import-untyped]
        except ImportError as exc:
            raise BridgeConnectionError(
                "clickhouse-driver is required for ClickHouse support. "
                "Install it with: pip install bridgebase[clickhouse]"
            ) from exc

        assert credentials is not None
        try:
            client = CHClient(
                host="127.0.0.1",
                port=proxy_port,
                user=credentials.username,
                password=credentials.password,
                database=self._database or "default",
            )
            client.execute("SELECT 1")
        except Exception as exc:
            raise BridgeConnectionError(f"ClickHouse connection failed: {exc}") from exc

        return client

    def _close_native(self, native_client: Any) -> None:
        try:
            native_client.disconnect()
        except Exception:
            pass
