"""PostgreSQL session — sets up gateway + proxy + credentials, returns native psycopg2 connection."""

from __future__ import annotations

import logging
from typing import Any, Optional

from bridgebase.base import BaseSession
from bridgebase.credentials import DatabaseCredentials
from bridgebase.exceptions import ConnectionError as BridgeConnectionError

logger = logging.getLogger("bridgebase.postgres")


class PostgresSession(BaseSession):
    """Session that returns the native ``psycopg2`` connection.

    Usage::

        session = PostgresSession(region="ap-south-1", jwt_token="...", database="app", ...)
        conn = session.connect()  # native psycopg2 connection
        cur = conn.cursor()
        cur.execute("SELECT 1")
        session.close()

        # Or with context manager:
        with PostgresSession(...) as conn:
            cur = conn.cursor()
            cur.execute("SELECT 1")
    """

    _db_label = "PostgreSQL"

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(db_type="postgres", **kwargs)

    # -- BaseSession hooks -------------------------------------------------

    def _connect_native(self, credentials: Optional[DatabaseCredentials], proxy_port: int) -> Any:
        try:
            import psycopg2  # type: ignore[import-untyped]
        except ImportError as exc:
            raise BridgeConnectionError(
                "psycopg2 is required for PostgreSQL support. "
                "Install it with: pip install bridgebase[postgres]"
            ) from exc

        assert credentials is not None
        try:
            conn = psycopg2.connect(
                host="127.0.0.1",
                port=proxy_port,
                user=credentials.username,
                password=credentials.password,
                dbname=self._database or "postgres",
            )
            conn.autocommit = True
        except Exception as exc:
            raise BridgeConnectionError(f"PostgreSQL connection failed: {exc}") from exc

        return conn

    def _close_native(self, native_client: Any) -> None:
        native_client.close()
