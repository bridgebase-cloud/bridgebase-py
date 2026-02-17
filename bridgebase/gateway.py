"""Gateway resolution and persistent control socket.

GatewayResolver  — resolves region → (host, port) via the control‑plane API.
GatewayConnection — manages the persistent authenticated TCP socket to the gateway.
"""

from __future__ import annotations

import logging
import socket
import ssl
import struct
import threading
from dataclasses import dataclass
from typing import Optional

import httpx

from bridgebase.exceptions import AuthError, GatewayError

logger = logging.getLogger("bridgebase.gateway")

# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------

_RESOLVE_PATH = "/v1/gateway/resolve"

# Max JWT size guard.
_MAX_JWT_SIZE: int = 8192


@dataclass(frozen=True, slots=True)
class GatewayEndpoint:
    """Resolved gateway host/port pair."""

    host: str
    port: int


# ---------------------------------------------------------------------------
# Resolver
# ---------------------------------------------------------------------------


class GatewayResolver:
    """Resolves the gateway endpoint for a given region.

    Results are cached per (region, api_base_url) pair for the lifetime of the
    resolver instance.  Thread‑safe.
    """

    def __init__(self, api_base_url: str) -> None:
        self._api_base_url = api_base_url.rstrip("/")
        self._cache: dict[str, GatewayEndpoint] = {}
        self._lock = threading.Lock()

    # -- public ------------------------------------------------------------

    def resolve(self, region: str, jwt_token: str) -> GatewayEndpoint:
        """Return the gateway endpoint for *region*, calling the API if needed."""
        with self._lock:
            if region in self._cache:
                return self._cache[region]

        # HTTP call outside the lock to avoid blocking other threads.
        endpoint = self._fetch(region, jwt_token)

        with self._lock:
            self._cache[region] = endpoint

        return endpoint

    def invalidate(self, region: str | None = None) -> None:
        """Clear cached endpoint(s)."""
        with self._lock:
            if region is None:
                self._cache.clear()
            else:
                self._cache.pop(region, None)

    # -- private -----------------------------------------------------------

    def _fetch(self, region: str, jwt_token: str) -> GatewayEndpoint:
        url = f"{self._api_base_url}{_RESOLVE_PATH}"
        headers = {"Authorization": f"Bearer {jwt_token}"}
        params = {"region": region}

        logger.debug("Resolving gateway for region=%s", region)

        try:
            with httpx.Client(timeout=10) as client:
                resp = client.get(url, headers=headers, params=params)
        except httpx.HTTPError as exc:
            raise GatewayError(f"Failed to reach gateway resolver: {exc}") from exc

        if resp.status_code == 401:
            raise AuthError("JWT rejected by gateway resolver")
        if resp.status_code != 200:
            raise GatewayError(
                f"Gateway resolver returned HTTP {resp.status_code}: {resp.text}"
            )

        data = resp.json()
        try:
            ep = GatewayEndpoint(host=data["gateway_host"], port=int(data["gateway_port"]))
        except (KeyError, ValueError, TypeError) as exc:
            raise GatewayError(f"Malformed resolver response: {exc}") from exc

        logger.debug("Resolved gateway → %s:%d", ep.host, ep.port)
        return ep


# ---------------------------------------------------------------------------
# Persistent Control Socket
# ---------------------------------------------------------------------------


class GatewayConnection:
    """Persistent authenticated TCP/TLS socket to the gateway.

    The socket is established lazily on the first call to :meth:`connect` and
    is reused for the lifetime of this object (or until :meth:`close` is
    called).  Thread‑safe.
    """

    def __init__(self, endpoint: GatewayEndpoint, jwt_token: str, *, use_tls: bool = True) -> None:
        self._endpoint = endpoint
        self._jwt_token = jwt_token
        self._use_tls = use_tls

        self._sock: Optional[socket.socket] = None
        self._lock = threading.Lock()
        self._connected = False

    # -- properties --------------------------------------------------------

    @property
    def connected(self) -> bool:
        return self._connected

    @property
    def socket(self) -> socket.socket:
        """Return the raw socket, connecting first if needed."""
        if not self._connected:
            self.connect()
        assert self._sock is not None
        return self._sock

    # -- public ------------------------------------------------------------

    def connect(self) -> None:
        """Open and authenticate the gateway socket (idempotent)."""
        with self._lock:
            if self._connected:
                return
            self._sock = self._open_socket()
            self._handshake()
            self._connected = True
            logger.debug(
                "Gateway socket established to %s:%d",
                self._endpoint.host,
                self._endpoint.port,
            )

    def close(self) -> None:
        """Close the socket gracefully."""
        with self._lock:
            if self._sock is not None:
                try:
                    self._sock.shutdown(socket.SHUT_RDWR)
                except OSError:
                    pass
                self._sock.close()
                self._sock = None
            self._connected = False
            logger.debug("Gateway socket closed")

    # -- private -----------------------------------------------------------

    def _open_socket(self) -> socket.socket:
        raw = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        raw.settimeout(10)
        try:
            if self._use_tls:
                ctx = ssl.create_default_context()
                sock = ctx.wrap_socket(raw, server_hostname=self._endpoint.host)
            else:
                sock = raw
            sock.connect((self._endpoint.host, self._endpoint.port))
            return sock
        except (OSError, ssl.SSLError) as exc:
            raw.close()
            raise GatewayError(
                f"Could not connect to gateway at "
                f"{self._endpoint.host}:{self._endpoint.port}: {exc}"
            ) from exc

    def _handshake(self) -> None:
        """Send JWT to authenticate with the gateway.

        Wire format:
            Client → Gateway
                [4B big‑endian token_len][token_len B jwt]
        """
        assert self._sock is not None
        token_bytes = self._jwt_token.encode("utf-8")
        if len(token_bytes) > _MAX_JWT_SIZE:
            raise GatewayError(f"JWT too large: {len(token_bytes)} bytes (max {_MAX_JWT_SIZE})")
        length_prefix = struct.pack(">I", len(token_bytes))
        try:
            self._sock.sendall(length_prefix)
            self._sock.sendall(token_bytes)
        except OSError as exc:
            raise GatewayError(f"Handshake I/O failure: {exc}") from exc

        logger.debug("JWT handshake sent (%d bytes)", len(token_bytes))
