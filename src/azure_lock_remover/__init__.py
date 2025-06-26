"""
Azure Lock Remover Package

A Python tool for removing management locks from Azure subscriptions.
"""

__version__ = "1.0.0"
__author__ = "Azure Lock Remover"

from .client import AzureLockRemover
from .exceptions import LockRemovalError, AuthenticationError, InvalidScopeError

__all__ = [
    "AzureLockRemover",
    "LockRemovalError",
    "AuthenticationError",
    "InvalidScopeError",
]
