"""Top‑level client factory.

Provides the ``Client`` factory class that creates sessions.  Each session
sets up the infrastructure (gateway, proxy, credentials) and returns the
**native** database client directly.

Usage::

    from bridgebase import Client

    sdk = Client(region="ap-south-1")

    # Context manager — returns native psycopg2 connection
    with sdk.pg(jwt_token="...", database="app") as conn:
        cur = conn.cursor()
        cur.execute("SELECT 1")
        print(cur.fetchall())

    # Or explicit connect/close
    session = sdk.tb(jwt_token="...")
    tb = session.connect()   # native tigerbeetle client
    tb.create_accounts([...])
    session.close()
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from bridgebase.clickhouse import ClickHouseSession
from bridgebase.mysql import MySQLSession
from bridgebase.postgres import PostgresSession
from bridgebase.redis import RedisSession
from bridgebase.tigerbeetle import TigerBeetleSession

logger = logging.getLogger("bridgebase.client")

_DEFAULT_API_BASE_URL = "https://api.bridgebase.io"


class Client:
    """Factory that creates sessions returning **native** database clients.

    Parameters
    ----------
    region:
        Cloud region identifier (e.g. ``"ap-south-1"``).
    api_base_url:
        Override the default control‑plane URL.
    use_tls:
        Whether gateway sockets use TLS (default ``True``).
    gateway_host:
        (Development) Skip resolver and connect directly to this host.
    gateway_port:
        (Development) Skip resolver and connect directly to this port.
    """

    def __init__(
        self,
        region: str,
        *,
        api_base_url: str = _DEFAULT_API_BASE_URL,
        use_tls: bool = True,
        gateway_host: Optional[str] = None,
        gateway_port: Optional[int] = None,
    ) -> None:
        self._region = region
        self._api_base_url = api_base_url
        self._use_tls = use_tls
        self._gateway_host = gateway_host
        self._gateway_port = gateway_port
        logger.debug("Client created for region=%s", region)

    # -- helpers -----------------------------------------------------------

    def _common_kwargs(
        self,
        jwt_token: str,
        database: Optional[str] = None,
    ) -> dict[str, Any]:
        return {
            "region": self._region,
            "jwt_token": jwt_token,
            "api_base_url": self._api_base_url,
            "database": database,
            "use_tls": self._use_tls,
            "gateway_host": self._gateway_host,
            "gateway_port": self._gateway_port,
        }

    # -- factory methods ---------------------------------------------------

    def pg(self, jwt_token: str, database: str) -> PostgresSession:
        """Create a PostgreSQL session.  Returns native psycopg2 connection via ``.connect()``."""
        return PostgresSession(**self._common_kwargs(jwt_token, database))

    def my(self, jwt_token: str, database: str) -> MySQLSession:
        """Create a MySQL session.  Returns native pymysql connection via ``.connect()``."""
        return MySQLSession(**self._common_kwargs(jwt_token, database))

    def rd(self, jwt_token: str, database: Optional[str] = None) -> RedisSession:
        """Create a Redis session.  Returns native redis.Redis via ``.connect()``."""
        return RedisSession(**self._common_kwargs(jwt_token, database))

    def ch(self, jwt_token: str, database: str) -> ClickHouseSession:
        """Create a ClickHouse session.  Returns native clickhouse_driver.Client via ``.connect()``."""
        return ClickHouseSession(**self._common_kwargs(jwt_token, database))

    def tb(self, jwt_token: str, *, cluster_id: int = 0) -> TigerBeetleSession:
        """Create a TigerBeetle session.  Returns native tigerbeetle client via ``.connect()``."""
        return TigerBeetleSession(cluster_id=cluster_id, **self._common_kwargs(jwt_token))
