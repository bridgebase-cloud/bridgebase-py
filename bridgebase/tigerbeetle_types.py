"""Re-export TigerBeetle library types and functions.

This module makes TigerBeetle types available through the BridgeBase SDK so users
don't have to import both ``bridgebase.tigerbeetle`` and the native ``tigerbeetle``
package.

Usage::

    from bridgebase import tigerbeetle

    # Access both session creation AND TigerBeetle types/functions
    with tigerbeetle(jwt_token="...") as tb_client:
        # Create types using the same module
        account = tigerbeetle.Account(...)
        transfer = tigerbeetle.Transfer(...)
        tb_client.create_accounts([account])
        tb_client.create_transfers([transfer])
"""

from __future__ import annotations

__all__ = []

# Lazy-import TigerBeetle types when the module is accessed
def __getattr__(name: str):
    try:
        import tigerbeetle as tb  # type: ignore[import-untyped]
        return getattr(tb, name)
    except ImportError as exc:
        raise ImportError(
            f"tigerbeetle package is required to use '{name}'. "
            f"Install it with: pip install bridgebase[tigerbeetle]"
        ) from exc


def __dir__():
    try:
        import tigerbeetle as tb  # type: ignore[import-untyped]
        return dir(tb)
    except ImportError:
        return []
