"""BridgeBase — Multi‑database SDK with gateway socket authentication.

Quick start::

    from bridgebase import tigerbeetle, redis

    # TigerBeetle
    with tigerbeetle(jwt_token="...") as tb:
        # Access TigerBeetle types through same import
        account = tigerbeetle.Account(id=tigerbeetle.id(), ledger=1, code=1)
        tb.create_accounts([account])

    # Redis / Valkey
    with redis(jwt_token="...") as rd:
        rd.set("key", "value")
"""

from __future__ import annotations

import logging
import sys
from typing import Any

from bridgebase.exceptions import (
    AuthError,
    BridgeBaseError,
    ConnectionError,
    CredentialError,
    GatewayError,
    GatewayResolutionError,
    ProxyError,
)
from bridgebase.redis import RedisSession
from bridgebase.tigerbeetle import TigerBeetleSession

logger = logging.getLogger("bridgebase")

_DEFAULT_API_BASE_URL = "https://api.bridgebase.dev"


def redis(
    jwt_token: str,
    *,
    db: int = 0,
    api_base_url: str = _DEFAULT_API_BASE_URL,
) -> RedisSession:
    """Create a Redis/Valkey session.

    Parameters
    ----------
    jwt_token : str
        JWT token for authentication.
    db : int, optional
        Redis database index (default: 0).
    api_base_url : str, optional
        Override default control-plane URL.

    Returns
    -------
    RedisSession
        Session that returns native redis.Redis via connect().

    Examples
    --------
    >>> from bridgebase import redis
    >>> with redis(jwt_token="...") as rd:
    ...     rd.set("key", "value")
    """
    return RedisSession(
        jwt_token=jwt_token,
        db=db,
        api_base_url=api_base_url,
        database=None,
    )

__all__ = [
    # Convenience functions
    "tigerbeetle",
    "redis",
    # Sessions
    "TigerBeetleSession",
    "RedisSession",
    # Exceptions
    "BridgeBaseError",
    "AuthError",
    "GatewayError",
    "GatewayResolutionError",
    "ConnectionError",
    "CredentialError",
    "ProxyError",
]

__version__ = "0.1.0"


# ── TigerBeetle namespace wrapper ──────────────────────────────────────
# This allows both:
#   from bridgebase import tigerbeetle
#   with tigerbeetle(jwt_token="...") as tb:  # Callable factory
#       account = tigerbeetle.Account(...)    # Type access


class _TigerBeetleNamespace:
    """Namespace that acts as both a session factory and type re-exporter."""

    def __call__(
        self,
        jwt_token: str,
        *,
        cluster_id: int = 0,
        api_base_url: str = _DEFAULT_API_BASE_URL,
    ) -> TigerBeetleSession:
        """Create a TigerBeetle session (callable).

        Parameters
        ----------
        jwt_token : str
            JWT token for authentication.
        cluster_id : int, optional
            TigerBeetle cluster ID (default: 0).
        api_base_url : str, optional
            Override default control-plane URL.

        Returns
        -------
        TigerBeetleSession
            Session that returns native tigerbeetle.ClientSync via connect().

        Examples
        --------
        >>> from bridgebase import tigerbeetle
        >>> with tigerbeetle(jwt_token="...") as tb:
        ...     account = tigerbeetle.Account(...)
        ...     tb.create_accounts([account])
        """
        return TigerBeetleSession(
            jwt_token=jwt_token,
            cluster_id=cluster_id,
            api_base_url=api_base_url,
            database=None,
        )

    def __getattr__(self, name: str) -> Any:
        """Lazily import and return attributes from the native tigerbeetle package."""
        if name in ("__wrapped__", "__doc__", "__module__"):
            return object.__getattribute__(self, name)

        try:
            import tigerbeetle as tb  # type: ignore[import-untyped]
            return getattr(tb, name)
        except ImportError as exc:
            raise ImportError(
                f"tigerbeetle package is required to access '{name}'. "
                f"Install it with: pip install bridgebase[tigerbeetle]"
            ) from exc

    def __dir__(self) -> list[str]:
        """Return attributes from native tigerbeetle package."""
        try:
            import tigerbeetle as tb  # type: ignore[import-untyped]
            return dir(tb)
        except ImportError:
            return []


# Replace the tigerbeetle function with the namespace wrapper
tigerbeetle = _TigerBeetleNamespace()
