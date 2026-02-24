"""TigerBeetle adapter for BridgeBase.

Quick start::

    from bridgebase.tigerbeetle import tigerbeetle

    with tigerbeetle(jwt_token="...") as tb:
        account = tigerbeetle.Account(id=1, ledger=1, code=1)
        tb.create_accounts([account])

TigerBeetle is a special case where the namespace provides both:
* A callable factory: ``tigerbeetle(jwt_token="...")`` → TigerBeetleSession
* Native type access: ``tigerbeetle.Account``, ``tigerbeetle.AccountFlags``, etc.
"""

from __future__ import annotations

from typing import Any

from bridgebase.tigerbeetle.session import TigerBeetleSession

__all__ = ["tigerbeetle", "TigerBeetleSession"]


class _TigerBeetleNamespace:
    """Namespace that acts as both a session factory and type re-exporter.

    Usage::

        from bridgebase.tigerbeetle import tigerbeetle

        # As a factory
        with tigerbeetle(jwt_token="...") as client:
            # Also access native types through same module
            account = tigerbeetle.Account(...)
            client.create_accounts([account])
    """

    def __call__(
        self,
        jwt_token: str,
        *,
        cluster_id: int = 0,
        api_base_url: str = "https://api.bridgebase.dev",
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
        >>> from bridgebase.tigerbeetle import tigerbeetle
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
        """Lazily import and return attributes from the native tigerbeetle package.

        This allows accessing tigerbeetle types like Account, Transfer, etc.
        through bridgebase.tigerbeetle without needing to import both.
        """
        if name in ("__wrapped__", "__doc__", "__module__"):
            return object.__getattribute__(self, name)

        try:
            import tigerbeetle as tb  # type: ignore[import-untyped]
            return getattr(tb, name)
        except ImportError as exc:
            raise ImportError(
                f"tigerbeetle package is required to access '{name}'. "
                f"Install it with: pip install bridgebase-tigerbeetle"
            ) from exc

    def __dir__(self) -> list[str]:
        """Return attributes from native tigerbeetle package."""
        try:
            import tigerbeetle as tb  # type: ignore[import-untyped]
            return dir(tb)
        except ImportError:
            return []


# Export the namespace as the module interface
tigerbeetle = _TigerBeetleNamespace()
