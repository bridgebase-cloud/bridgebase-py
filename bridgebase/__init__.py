"""BridgeBase — multi‑database SDK with gateway socket + session‑based credentials.

Quick start::

    from bridgebase import Client

    sdk = Client(region="ap-south-1")

    # Context manager returns the native DB client directly
    with sdk.pg(jwt_token="...", database="app") as conn:
        cur = conn.cursor()
        cur.execute("SELECT 1")

    # Or explicit connect / close
    session = sdk.tb(jwt_token="...")
    tb = session.connect()   # native tigerbeetle client
    tb.create_accounts([...])
    session.close()
"""

from bridgebase.clickhouse import ClickHouseSession
from bridgebase.client import Client
from bridgebase.exceptions import (
    AuthError,
    BridgeBaseError,
    ConnectionError,
    CredentialError,
    GatewayError,
    ProxyError,
)
from bridgebase.mysql import MySQLSession
from bridgebase.postgres import PostgresSession
from bridgebase.redis import RedisSession
from bridgebase.tigerbeetle import TigerBeetleSession

__all__ = [
    "Client",
    # Sessions
    "PostgresSession",
    "MySQLSession",
    "RedisSession",
    "ClickHouseSession",
    "TigerBeetleSession",
    # Exceptions
    "BridgeBaseError",
    "AuthError",
    "GatewayError",
    "ConnectionError",
    "CredentialError",
    "ProxyError",
]

__version__ = "0.1.0"
