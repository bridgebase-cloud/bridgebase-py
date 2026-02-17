"""Credential retrieval and release via the control‑plane API.

Phase‑1: no TTL, no auto‑refresh.  Credentials are session‑bound and
rotated on release.  The module is structured so Phase‑2 TTL / refresh
logic can be added inside `CredentialClient` without touching callers.
"""

from __future__ import annotations

import logging
import threading
from dataclasses import dataclass
from typing import Optional

import httpx

from bridgebase.exceptions import AuthError, CredentialError

logger = logging.getLogger("bridgebase.credentials")

_CREDENTIALS_PATH = "/v1/db/credentials"
_RELEASE_PATH = "/v1/db/release"


@dataclass(frozen=True, slots=True)
class DatabaseCredentials:
    """Opaque credential bundle returned by the gateway."""

    username: str
    password: str
    host: str
    port: int


class CredentialClient:
    """Fetches and releases session‑bound database credentials.

    Thread‑safe.  A single instance can be shared across callers with
    different JWT tokens.

    Phase‑2 hooks
    -------------
    * ``ttl`` / ``expires_at`` can be added to ``DatabaseCredentials``.
    * A background refresh timer can be started in :meth:`fetch`.
    * :meth:`release` already notifies the gateway for credential rotation.
    """

    def __init__(self, api_base_url: str) -> None:
        self._api_base_url = api_base_url.rstrip("/")
        self._lock = threading.Lock()

    # -- public ------------------------------------------------------------

    def fetch(
        self,
        jwt_token: str,
        database: Optional[str] = None,
        db_type: Optional[str] = None,
    ) -> DatabaseCredentials:
        """Retrieve a fresh credential set from the gateway.

        Parameters
        ----------
        jwt_token:
            Bearer token for authentication.
        database:
            Database name (required for PG, MySQL, ClickHouse; optional for Redis).
        db_type:
            Hint for the gateway so it knows which pool to allocate from
            (e.g. ``"postgres"``, ``"mysql"``).
        """
        url = f"{self._api_base_url}{_CREDENTIALS_PATH}"
        headers = {"Authorization": f"Bearer {jwt_token}"}
        body: dict[str, str] = {}
        if database is not None:
            body["database"] = database
        if db_type is not None:
            body["db_type"] = db_type

        logger.debug("Requesting credentials (db_type=%s, database=%s)", db_type, database)

        try:
            with httpx.Client(timeout=10) as client:
                resp = client.post(url, headers=headers, json=body)
        except httpx.HTTPError as exc:
            raise CredentialError(f"Credential request failed: {exc}") from exc

        if resp.status_code == 401:
            raise AuthError("JWT rejected by credential service")
        if resp.status_code != 200:
            raise CredentialError(
                f"Credential service returned HTTP {resp.status_code}: {resp.text}"
            )

        data = resp.json()
        try:
            creds = DatabaseCredentials(
                username=data["username"],
                password=data["password"],
                host=data["host"],
                port=int(data["port"]),
            )
        except (KeyError, ValueError, TypeError) as exc:
            raise CredentialError(f"Malformed credential response: {exc}") from exc

        logger.debug(
            "Credentials obtained for user=%s host=%s:%d", creds.username, creds.host, creds.port
        )
        return creds

    def release(self, jwt_token: str, username: str) -> None:
        """Notify the gateway to rotate the credential and return it to the pool.

        This MUST be called when the client closes its connection.
        """
        url = f"{self._api_base_url}{_RELEASE_PATH}"
        headers = {"Authorization": f"Bearer {jwt_token}"}
        body = {"username": username}

        logger.debug("Releasing credential for user=%s", username)

        try:
            with httpx.Client(timeout=10) as client:
                resp = client.post(url, headers=headers, json=body)
        except httpx.HTTPError as exc:
            # Best‑effort — log but don't crash on release failure.
            logger.warning("Credential release request failed: %s", exc)
            return

        if resp.status_code != 200:
            logger.warning(
                "Credential release returned HTTP %d: %s",
                resp.status_code,
                resp.text,
            )
        else:
            logger.debug("Credential released successfully")
