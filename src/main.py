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

from azure_lock_remover import AzureLockRemover
from azure_lock_remover.utils import setup_logging, validate_subscription_id


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
        # Validate subscription ID format
        if not validate_subscription_id(args.subscription_id):
            logger.error("Invalid subscription ID format. Expected GUID format.")
            sys.exit(1)

        # Initialize and run lock remover
        remover = AzureLockRemover(
            subscription_id=args.subscription_id, dry_run=args.dry_run
        )

        if args.dry_run:
            logger.info("Running in DRY RUN mode - no locks will be removed")

        result = remover.remove_all_locks()

        # Log final summary
        if result["total"] == 0:
            logger.info("No management locks found in subscription")
        else:
            action = "would be processed" if args.dry_run else "processed"
            logger.info(
                f"Lock removal completed: {result['success']}/{result['total']} "
                f"locks {action} successfully"
            )

        logger.info("Lock removal process completed successfully")

    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Script failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
