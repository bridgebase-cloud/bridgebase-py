"""TigerBeetle session — sets up gateway + proxy, returns native client.

TigerBeetle is a special case: the JWT is only used for gateway
authentication.  No username/password credentials are involved.
The native ``tigerbeetle`` client is returned directly.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from bridgebase.core import BaseSession, DatabaseCredentials
from bridgebase.core import ConnectionError as BridgeConnectionError

logger = logging.getLogger("bridgebase.tigerbeetle.session")


class TigerBeetleSession(BaseSession):
    """Session that returns the native ``tigerbeetle`` client.

    Usage::

        session = TigerBeetleSession(jwt_token="...", ...)
        tb = session.connect()  # native tigerbeetle client
        tb.create_accounts([...])
        session.close()

        # Or with context manager:
        with TigerBeetleSession(...) as tb:
            tb.create_accounts([...])
    """

    _db_label = "TigerBeetle"

    def __init__(self, *, cluster_id: int = 0, **kwargs: Any) -> None:
        super().__init__(db_type="tigerbeetle", **kwargs)
        self._cluster_id = cluster_id

    # -- BaseSession hooks -------------------------------------------------

    @property
    def _requires_credentials(self) -> bool:
        return False

    def _connect_native(self, credentials: Optional[DatabaseCredentials], proxy_port: int) -> Any:
        try:
            import tigerbeetle as tb  # type: ignore[import-untyped]
        except ImportError as exc:
            raise BridgeConnectionError(
                "tigerbeetle is required for TigerBeetle support. "
                "Install it with: pip install bridgebase-tigerbeetle"
            ) from exc

        try:
            client = tb.ClientSync(
                cluster_id=self._cluster_id,
                replica_addresses=f"127.0.0.1:{proxy_port}",
            )
        except Exception as exc:
            raise BridgeConnectionError(f"TigerBeetle connection failed: {exc}") from exc

        return client

    def _close_native(self, native_client: Any) -> None:
        try:
            native_client.close()
        except Exception:
            pass
