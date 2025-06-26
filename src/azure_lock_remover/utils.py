"""
Configuration and utilities
"""

import logging


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


def validate_subscription_id(subscription_id: str) -> bool:
    """
    Validate Azure subscription ID format.

    Args:
        subscription_id: The subscription ID to validate

    Returns:
        True if valid format, False otherwise
    """
    return len(subscription_id) == 36 and subscription_id.count("-") == 4
