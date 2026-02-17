"""Abstract base session that every DB adapter inherits from.

``BaseSession`` encapsulates the full Phase‑1 lifecycle:

    connect() → resolve gateway → open control socket → start proxy
    → connect native driver → return native client

    close() → close native → stop proxy → release credentials → close gateway

Subclasses only implement two hooks:
    ``_connect_native``      — create and return the real DB client
    ``_close_native``        — tear down the real DB client
    ``_requires_credentials`` — whether this DB type needs creds (False for TB)

The SDK never wraps native methods.  ``connect()`` returns the original
library client so users get full access to every feature and future update.
"""

from __future__ import annotations

import logging
import threading
from abc import ABC, abstractmethod
from typing import Any, Optional

from bridgebase.credentials import CredentialClient, DatabaseCredentials
from bridgebase.exceptions import ConnectionError as BridgeConnectionError
from bridgebase.gateway import GatewayConnection, GatewayEndpoint, GatewayResolver
from bridgebase.proxy import ProxyManager

logger = logging.getLogger("bridgebase.base")


class BaseSession(ABC):
    """Abstract base for all database sessions.

    Parameters
    ----------
    jwt_token:
        Bearer JWT for gateway authentication.
    api_base_url:
        Root URL of the control‑plane API.
    database:
        Database name (required for SQL stores).
    db_type:
        Discriminator string sent to the credential service.
    """

    # Subclasses should set this to a human‑friendly label for logging.
    _db_label: str = "unknown"

    def __init__(
        self,
        *,
        jwt_token: str,
        api_base_url: str,
        database: Optional[str] = None,
        db_type: Optional[str] = None,
    ) -> None:
        self._jwt_token = jwt_token
        self._api_base_url = api_base_url
        self._database = database
        self._db_type = db_type

        # Internal components — created lazily.
        self._resolver = GatewayResolver(api_base_url)
        self._credential_client = CredentialClient(api_base_url)
        self._gateway_conn: Optional[GatewayConnection] = None
        self._proxy = ProxyManager()
        self._credentials: Optional[DatabaseCredentials] = None
        self._native_client: Any = None

        self._initialized = False
        self._closed = False
        self._lock = threading.Lock()

    # -- abstract hooks (subclass contract) --------------------------------

    @abstractmethod
    def _connect_native(self, credentials: Optional[DatabaseCredentials], proxy_port: int) -> Any:
        """Create and **return** the native DB client.

        For TigerBeetle, *credentials* will be ``None``.
        """

    @abstractmethod
    def _close_native(self, native_client: Any) -> None:
        """Close the native DB client."""

    @property
    def _requires_credentials(self) -> bool:
        """Return ``True`` if the adapter needs username/password credentials."""
        return True

    # -- public API --------------------------------------------------------

    def connect(self) -> Any:
        """Set up infrastructure and return the **native** database client.

        Idempotent — calling connect() again returns the same client.
        """
        if self._initialized:
            return self._native_client
        with self._lock:
            if self._initialized:
                return self._native_client
            if self._closed:
                raise BridgeConnectionError(f"{self._db_label} session has already been closed")
            self._native_client = self._do_initialize()
            self._initialized = True
        return self._native_client

    def close(self) -> None:
        """Tear down everything — native client, proxy, credentials, gateway socket."""
        with self._lock:
            if self._closed:
                return
            self._closed = True

        # Step 8‑1: close native connection
        if self._native_client is not None:
            try:
                self._close_native(self._native_client)
            except Exception:
                logger.warning("Error closing native %s connection", self._db_label, exc_info=True)
            self._native_client = None

        # Step 8‑2: stop proxy
        self._proxy.stop()

        # Step 8‑3: release credentials
        if self._credentials is not None:
            self._credential_client.release(self._jwt_token, self._credentials.username)

        # Step 8‑4: close gateway socket
        if self._gateway_conn is not None:
            self._gateway_conn.close()

        logger.info("%s session closed", self._db_label)

    # -- context manager ---------------------------------------------------

    def __enter__(self) -> Any:
        """Connect and return the native client directly."""
        return self.connect()

    def __exit__(self, *_exc: Any) -> None:
        self.close()

    # -- private -----------------------------------------------------------

    def _do_initialize(self) -> Any:
        """Execute the full Phase‑1 bring‑up sequence.  Returns native client."""
        # Step 2: resolve gateway
        endpoint = self._resolver.resolve(self._jwt_token)

        # Step 3: open control socket
        self._gateway_conn = GatewayConnection(endpoint, self._jwt_token)
        self._gateway_conn.connect()

        # Step 6: start local proxy
        proxy_port = self._proxy.start(self._gateway_conn.socket)

        # Step 4 (optional): fetch credentials
        if self._requires_credentials:
            self._credentials = self._credential_client.fetch(
                jwt_token=self._jwt_token,
                database=self._database,
                db_type=self._db_type,
            )

        # Step 5: connect native driver and return it
        native_client = self._connect_native(self._credentials, proxy_port)

        logger.info(
            "%s session initialized (proxy=127.0.0.1:%d)",
            self._db_label,
            proxy_port,
        )
        return native_client
