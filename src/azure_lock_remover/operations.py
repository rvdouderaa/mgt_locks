"""
Azure Management Lock operations
"""

import logging
from typing import List, Any

from azure.core.exceptions import HttpResponseError, ResourceNotFoundError

from .auth import AzureAuthManager
from .parser import LockScopeParser
from .retry import RetryManager


class LockOperations:
    """Handles Azure management lock operations."""

    def __init__(self, auth_manager: AzureAuthManager, dry_run: bool = False):
        """
        Initialize lock operations.

        Args:
            auth_manager: Azure authentication manager
            dry_run: If True, only simulate operations
        """
        self.auth_manager = auth_manager
        self.dry_run = dry_run
        self.logger = logging.getLogger(__name__)
        self.parser = LockScopeParser()
        self.retry_manager = RetryManager()

    def list_locks(self) -> List[Any]:
        """
        List all management locks in the subscription.

        Returns:
            List of ManagementLockObject instances
        """
        try:
            self.logger.info("Retrieving management locks from subscription...")

            def _list_locks():
                client = self.auth_manager.client
                return list(client.management_locks.list_at_subscription_level())

            locks = self.retry_manager.retry_with_backoff(_list_locks)
            self.logger.info(f"Found {len(locks)} management locks")

            return locks

        except ResourceNotFoundError:
            self.logger.warning("Subscription not found or no access")
            return []
        except HttpResponseError as e:
            self.logger.error(f"HTTP error while listing locks: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error while listing locks: {e}")
            raise

    def remove_lock(self, lock: Any) -> bool:
        """
        Remove a specific management lock.

        Args:
            lock: ManagementLockObject to remove

        Returns:
            True if successful, False otherwise
        """
        try:
            lock_name = lock.name
            lock_scope = lock.id.split("/providers/Microsoft.Authorization/locks/")[0]

            if self.dry_run:
                self.logger.info(
                    f"[DRY RUN] Would remove lock: {lock_name} (scope: {lock_scope})"
                )
                return True

            self.logger.info(f"Removing lock: {lock_name} (scope: {lock_scope})")

            def _delete_lock():
                self._execute_delete_operation(lock_name, lock_scope)

            self.retry_manager.retry_with_backoff(_delete_lock)
            self.logger.info(f"Successfully removed lock: {lock_name}")
            return True

        except ResourceNotFoundError:
            self.logger.warning(
                f"Lock {lock.name} not found (may have been removed already)"
            )
            return True
        except HttpResponseError as e:
            if e.status_code == 403:
                self.logger.error(
                    f"Insufficient permissions to remove lock: {lock.name}"
                )
            else:
                self.logger.error(f"HTTP error removing lock {lock.name}: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error removing lock {lock.name}: {e}")
            return False

    def _execute_delete_operation(self, lock_name: str, lock_scope: str) -> None:
        """Execute the appropriate delete operation based on lock scope."""
        scope_info = self.parser.parse_lock_scope(lock_scope)
        client = self.auth_manager.client

        if scope_info["type"] == "resource_group":
            rg_name = scope_info["resource_group_name"]
            self.logger.debug(
                f"Deleting resource group lock: {lock_name} from RG: {rg_name}"
            )
            client.management_locks.delete_at_resource_group_level(
                resource_group_name=rg_name, lock_name=lock_name
            )
        elif scope_info["type"] == "resource":
            provider = scope_info["provider"]
            resource_type = scope_info["resource_type"]
            resource_name = scope_info["resource_name"]
            self.logger.debug(
                f"Deleting resource lock: {lock_name} from "
                f"{provider}/{resource_type}/{resource_name}"
            )
            client.management_locks.delete_at_resource_level(
                resource_group_name=scope_info["resource_group_name"],
                resource_provider_namespace=scope_info["provider"],
                parent_resource_path="",
                resource_type=scope_info["resource_type"],
                resource_name=scope_info["resource_name"],
                lock_name=lock_name,
            )
        elif scope_info["type"] == "subscription":
            self.logger.debug(f"Deleting subscription lock: {lock_name}")
            client.management_locks.delete_at_subscription_level(lock_name=lock_name)
        else:
            raise ValueError(f"Unknown lock scope type: {scope_info['type']}")

    def remove_all_locks(self) -> dict:
        """
        Remove all management locks in the subscription.

        Returns:
            Dictionary with operation summary
        """
        try:
            locks = self.list_locks()

            if not locks:
                self.logger.info("No management locks found in subscription")
                return {"total": 0, "success": 0, "failed": 0}

            self.logger.info(f"Processing {len(locks)} locks...")

            success_count = 0
            failure_count = 0

            for lock in locks:
                self.logger.info(f"Processing lock: {lock.name} (Level: {lock.level})")

                if self.remove_lock(lock):
                    success_count += 1
                else:
                    failure_count += 1

            # Summary
            action = "would be removed" if self.dry_run else "removed"
            self.logger.info(f"Summary: {success_count} locks {action} successfully")

            if failure_count > 0:
                self.logger.warning(f"{failure_count} locks failed to be removed")

            return {
                "total": len(locks),
                "success": success_count,
                "failed": failure_count,
            }

        except Exception as e:
            self.logger.error(f"Failed to remove locks: {e}")
            raise
