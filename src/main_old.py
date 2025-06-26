#!/usr/bin/env python3
"""
Azure Subscription Lock Removal Tool

This script removes all management locks from an Azure subscription.
It uses Azure SDK for Python with managed identity or interactive authentication.

Usage:
    python main.py --subscription-id <subscription-id>
    python main.py --subscription-id <subscription-id> --dry-run
    python main.py --subscription-id <subscription-id> --log-level DEBUG

Requirements:
    - azure-mgmt-resource
    - azure-identity
    - azure-core

Authentication:
    - Managed Identity (when running on Azure)
    - Interactive Browser (when running locally)
    - Service Principal (via environment variables)
"""

import argparse
import logging
import sys
import time
from typing import List, Any, Optional

from azure.core.exceptions import (
    HttpResponseError,
    ClientAuthenticationError,
    ResourceNotFoundError,
    ServiceRequestError,
)
from azure.identity import DefaultAzureCredential
from azure.mgmt.resource import ManagementLockClient


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
        self.client: Optional[ManagementLockClient] = (
            None  # Will be initialized in _initialize_client
        )

        # Initialize Azure credentials and client
        self._initialize_client()

    def _initialize_client(self) -> None:
        """Initialize Azure Management Lock client with appropriate credentials."""
        try:
            # Use DefaultAzureCredential which handles multiple auth methods:
            # 1. Managed Identity (when running on Azure)
            # 2. Environment variables (service principal)
            # 3. Azure CLI (if logged in)
            # 4. Interactive browser (fallback)
            credential = DefaultAzureCredential()

            self.client = ManagementLockClient(
                credential=credential, subscription_id=self.subscription_id
            )

            self.logger.info(
                f"Initialized Azure client for subscription: {self.subscription_id}"
            )

        except ClientAuthenticationError as e:
            self.logger.error(f"Authentication failed: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Failed to initialize Azure client: {e}")
            raise

    def _retry_with_backoff(self, func, max_retries: int = 3, base_delay: float = 1.0):
        """
        Execute function with exponential backoff retry logic.

        Args:
            func: Function to execute
            max_retries: Maximum number of retry attempts
            base_delay: Base delay in seconds for exponential backoff
        """
        for attempt in range(max_retries + 1):
            try:
                return func()
            except (ServiceRequestError, HttpResponseError) as e:
                if attempt == max_retries:
                    raise

                delay = base_delay * (2**attempt)
                self.logger.warning(
                    f"Attempt {attempt + 1} failed: {e}. Retrying in {delay} seconds..."
                )
                time.sleep(delay)

    def list_locks(self) -> List[Any]:
        """
        List all management locks in the subscription.

        Returns:
            List of ManagementLockObject instances
        """
        if self.client is None:
            raise RuntimeError("Azure client not initialized")

        try:
            self.logger.info("Retrieving management locks from subscription...")

            def _list_locks():
                return list(self.client.management_locks.list_at_subscription_level())  # type: ignore

            locks = self._retry_with_backoff(_list_locks)
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
        if self.client is None:
            raise RuntimeError("Azure client not initialized")

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
                # Determine lock scope and use appropriate deletion method
                scope_lower = lock_scope.lower()

                if "/resourcegroups/" in scope_lower:
                    # Split on case-insensitive "resourcegroups" but preserve original case for extraction
                    # Find the position of "resourcegroups" in the original scope
                    rg_index = scope_lower.find("/resourcegroups/")
                    if rg_index == -1:
                        raise ValueError(
                            f"Could not find resourcegroups in scope: {lock_scope}"
                        )

                    # Extract everything after "/resourcegroups/"
                    after_rg = lock_scope[rg_index + len("/resourcegroups/") :]

                    if "/providers/" not in after_rg:
                        # Resource group scoped lock
                        # Format: /subscriptions/{sub-id}/resourcegroups/{rg-name}
                        rg_name = after_rg.rstrip(
                            "/"
                        )  # Remove trailing slash if present
                        self.logger.debug(
                            f"Deleting resource group lock: {lock_name} from RG: {rg_name}"
                        )
                        self.client.management_locks.delete_at_resource_group_level(  # type: ignore
                            resource_group_name=rg_name, lock_name=lock_name
                        )
                    else:
                        # Resource scoped lock
                        # Format: /subscriptions/{sub-id}/resourcegroups/{rg-name}/providers/{provider}/{resource-type}/{resource-name}
                        parts = after_rg.split("/")
                        if (
                            len(parts) < 4
                        ):  # Need at least: rg-name, providers, provider-name, resource-type
                            raise ValueError(
                                f"Invalid resource lock scope format: {lock_scope}"
                            )

                        rg_name = parts[0]

                        # Find "providers" in the parts
                        try:
                            providers_index = next(
                                i
                                for i, part in enumerate(parts)
                                if part.lower() == "providers"
                            )
                        except StopIteration:
                            raise ValueError(
                                f"Could not find providers in scope: {lock_scope}"
                            )

                        if providers_index + 2 >= len(parts):
                            raise ValueError(
                                f"Invalid provider format in scope: {lock_scope}"
                            )

                        provider = parts[providers_index + 1]
                        resource_type = parts[providers_index + 2]

                        # Resource name could be the next part or multiple parts combined
                        if providers_index + 3 < len(parts):
                            resource_name = "/".join(parts[providers_index + 3 :])
                        else:
                            raise ValueError(
                                f"Could not find resource name in scope: {lock_scope}"
                            )

                        self.logger.debug(
                            f"Deleting resource lock: {lock_name} from {provider}/{resource_type}/{resource_name}"
                        )
                        self.client.management_locks.delete_at_resource_level(  # type: ignore
                            resource_group_name=rg_name,
                            resource_provider_namespace=provider,
                            parent_resource_path="",
                            resource_type=resource_type,
                            resource_name=resource_name,
                            lock_name=lock_name,
                        )
                else:
                    # Subscription scoped lock
                    # Format: /subscriptions/{sub-id}
                    self.logger.debug(f"Deleting subscription lock: {lock_name}")
                    self.client.management_locks.delete_at_subscription_level(  # type: ignore
                        lock_name=lock_name
                    )

            self._retry_with_backoff(_delete_lock)
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

    def remove_all_locks(self) -> None:
        """Remove all management locks in the subscription."""
        try:
            locks = self.list_locks()

            if not locks:
                self.logger.info("No management locks found in subscription")
                return

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

        except Exception as e:
            self.logger.error(f"Failed to remove locks: {e}")
            raise


def setup_logging(log_level: str) -> None:
    """Configure logging with the specified level."""
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f"Invalid log level: {log_level}")

    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Remove all management locks from an Azure subscription",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --subscription-id 12345678-1234-1234-1234-123456789012
  %(prog)s --subscription-id 12345678-1234-1234-1234-123456789012 --dry-run
  %(prog)s --subscription-id 12345678-1234-1234-1234-123456789012 --log-level DEBUG

Authentication:
  The script uses DefaultAzureCredential which supports:
  - Managed Identity (when running on Azure)
  - Service Principal via environment variables
  - Azure CLI credentials
  - Interactive browser authentication

Required Permissions:
  - Microsoft.Authorization/locks/read
  - Microsoft.Authorization/locks/delete
        """,
    )

    parser.add_argument(
        "--subscription-id", required=True, help="Azure subscription ID"
    )

    parser.add_argument(
        "--dry-run", action="store_true", help="List locks without removing them"
    )

    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level (default: INFO)",
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging(args.log_level)
    logger = logging.getLogger(__name__)

    try:
        # Validate subscription ID format (basic check)
        if len(args.subscription_id) != 36 or args.subscription_id.count("-") != 4:
            logger.error("Invalid subscription ID format. Expected GUID format.")
            sys.exit(1)

        # Initialize and run lock remover
        remover = AzureLockRemover(
            subscription_id=args.subscription_id, dry_run=args.dry_run
        )

        if args.dry_run:
            logger.info("Running in DRY RUN mode - no locks will be removed")

        remover.remove_all_locks()
        logger.info("Lock removal process completed successfully")

    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Script failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
