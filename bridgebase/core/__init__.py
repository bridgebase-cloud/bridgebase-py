"""BridgeBase Core — Database-agnostic infrastructure for gateway-authenticated connections.

This module provides the foundation for all BridgeBase adapters:

* BaseSession — abstract base for database-specific session implementations
* GatewayResolver — resolves gateway endpoints via the control-plane API
* GatewayConnection — persistent authenticated TCP socket to the gateway
* ProxyManager — local TCP proxy that tunnels traffic through the gateway
* CredentialClient — fetches and releases database credentials
* Exception hierarchy — all BridgeBase errors

Adapters (redis, tigerbeetle, mysql, etc.) depend on core and implement
their own session subclass and convenience function.
"""

from __future__ import annotations

from bridgebase.core.base import BaseSession
from bridgebase.core.credentials import CredentialClient, DatabaseCredentials
from bridgebase.core.exceptions import (
    AuthError,
    BridgeBaseError,
    ConnectionError,
    CredentialError,
    GatewayError,
    GatewayResolutionError,
    ProxyError,
)
from bridgebase.core.gateway import GatewayConnection, GatewayEndpoint, GatewayResolver
from bridgebase.core.proxy import ProxyManager

__all__ = [
    # Base session
    "BaseSession",
    # Gateway
    "GatewayResolver",
    "GatewayConnection",
    "GatewayEndpoint",
    # Proxy
    "ProxyManager",
    # Credentials
    "CredentialClient",
    "DatabaseCredentials",
    # Exceptions
    "BridgeBaseError",
    "AuthError",
    "GatewayError",
    "GatewayResolutionError",
    "ConnectionError",
    "CredentialError",
    "ProxyError",
]

__version__ = "0.2.0"
