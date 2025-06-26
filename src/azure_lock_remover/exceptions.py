"""
Custom exceptions for Azure Lock Remover
"""


class LockRemovalError(Exception):
    """Base exception for lock removal operations."""

    pass


class AuthenticationError(LockRemovalError):
    """Raised when authentication fails."""

    pass


class InvalidScopeError(LockRemovalError):
    """Raised when lock scope cannot be parsed."""

    pass


class AzureClientError(LockRemovalError):
    """Raised when Azure client operations fail."""

    pass


class PermissionError(LockRemovalError):
    """Raised when insufficient permissions to perform operation."""

    pass
