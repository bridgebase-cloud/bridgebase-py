"""Custom exceptions for the BridgeBase SDK.

All exceptions inherit from BridgeBaseError to allow catching any SDK error.
Secrets (JWTs, passwords) are never included in exception messages.
"""

from __future__ import annotations


class BridgeBaseError(Exception):
    """Base exception for all BridgeBase SDK errors."""


class AuthError(BridgeBaseError):
    """Raised when JWT authentication fails (invalid, expired, or rejected)."""


class GatewayError(BridgeBaseError):
    """Raised when gateway resolution or the control socket encounters an error."""


class GatewayResolutionError(GatewayError):
    """Raised when the gateway resolve API call fails."""


class ConnectionError(BridgeBaseError):  # noqa: A001 — intentional shadow of builtin
    """Raised when the native database connection fails."""


class ProxyError(BridgeBaseError):
    """Raised when the local TCP proxy encounters an error."""


class CredentialError(BridgeBaseError):
    """Raised when credential retrieval or release fails."""
