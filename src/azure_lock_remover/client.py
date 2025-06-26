"""
Main client class for Azure Lock Remover
"""

import logging

from .auth import AzureAuthManager
from .operations import LockOperations


class AzureLockRemover:
    """
    Azure Management Lock Removal Tool

    Handles the removal of all management locks in an Azure subscription
    with proper error handling, retry logic, and logging.
    """

    def __init__(self, subscription_id: str, dry_run: bool = False):
        """
        Initialize the lock remover.

        Args:
            subscription_id: Azure subscription ID
            dry_run: If True, only list locks without removing them
        """
        self.subscription_id = subscription_id
        self.dry_run = dry_run
        self.logger = logging.getLogger(__name__)

        # Initialize components
        self.auth_manager = AzureAuthManager(subscription_id)
        self.operations = LockOperations(self.auth_manager, dry_run)

    def list_locks(self):
        """List all management locks in the subscription."""
        return self.operations.list_locks()

    def remove_lock(self, lock):
        """Remove a specific management lock."""
        return self.operations.remove_lock(lock)

    def remove_all_locks(self):
        """Remove all management locks in the subscription."""
        return self.operations.remove_all_locks()
