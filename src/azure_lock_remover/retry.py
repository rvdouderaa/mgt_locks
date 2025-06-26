"""
Retry logic utilities
"""

import logging
import time
from typing import Callable, TypeVar

from azure.core.exceptions import HttpResponseError, ServiceRequestError

T = TypeVar("T")


class RetryManager:
    """Handles retry logic with exponential backoff."""

    def __init__(self, max_retries: int = 3, base_delay: float = 1.0):
        """
        Initialize retry manager.

        Args:
            max_retries: Maximum number of retry attempts
            base_delay: Base delay in seconds for exponential backoff
        """
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.logger = logging.getLogger(__name__)

    def retry_with_backoff(self, func: Callable[[], T]) -> T:
        """
        Execute function with exponential backoff retry logic.

        Args:
            func: Function to execute

        Returns:
            Result of the function execution

        Raises:
            The last exception if all retries fail
        """
        for attempt in range(self.max_retries + 1):
            try:
                return func()
            except (ServiceRequestError, HttpResponseError) as e:
                if attempt == self.max_retries:
                    raise

                delay = self.base_delay * (2**attempt)
                self.logger.warning(
                    f"Attempt {attempt + 1} failed: {e}. Retrying in {delay} seconds..."
                )
                time.sleep(delay)

        # This should never be reached due to the raise in the except block
        raise RuntimeError("All retry attempts failed")
