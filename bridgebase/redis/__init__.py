"""Redis / Valkey adapter for BridgeBase.

Quick start::

    from bridgebase.redis import redis

    with redis(jwt_token="...") as rd:
        rd.set("key", "value")
        print(rd.get("key"))
"""

from __future__ import annotations

from bridgebase.redis.session import RedisSession

__all__ = ["redis", "RedisSession"]


def redis(
    jwt_token: str,
    *,
    db: int = 0,
    api_base_url: str = "https://api.bridgebase.dev",
) -> RedisSession:
    """Create a Redis/Valkey session with gateway authentication.

    Returns directly connect to the native redis.Redis client via the local proxy.

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
    >>> from bridgebase.redis import redis
    >>> with redis(jwt_token="...") as rd:
    ...     rd.set("key", "value")
    """
    return RedisSession(
        jwt_token=jwt_token,
        db=db,
        api_base_url=api_base_url,
        database=None,
    )
