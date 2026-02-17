"""MySQL session — sets up gateway + proxy + credentials, returns native pymysql connection."""

from __future__ import annotations

import logging
from typing import Any, Optional

from bridgebase.base import BaseSession
from bridgebase.credentials import DatabaseCredentials
from bridgebase.exceptions import ConnectionError as BridgeConnectionError

logger = logging.getLogger("bridgebase.mysql")


class MySQLSession(BaseSession):
    """Session that returns the native ``pymysql`` connection.

    Usage::

        session = MySQLSession(region="ap-south-1", jwt_token="...", database="app", ...)
        conn = session.connect()  # native pymysql connection
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
        session.close()

        # Or with context manager:
        with MySQLSession(...) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
    """

    _db_label = "MySQL"

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(db_type="mysql", **kwargs)

    # -- BaseSession hooks -------------------------------------------------

    def _connect_native(self, credentials: Optional[DatabaseCredentials], proxy_port: int) -> Any:
        try:
            import pymysql  # type: ignore[import-untyped]
        except ImportError as exc:
            raise BridgeConnectionError(
                "pymysql is required for MySQL support. "
                "Install it with: pip install bridgebase[mysql]"
            ) from exc

        assert credentials is not None
        try:
            conn = pymysql.connect(
                host="127.0.0.1",
                port=proxy_port,
                user=credentials.username,
                password=credentials.password,
                database=self._database or "",
                autocommit=True,
            )
        except Exception as exc:
            raise BridgeConnectionError(f"MySQL connection failed: {exc}") from exc

        return conn

    def _close_native(self, native_client: Any) -> None:
        native_client.close()
