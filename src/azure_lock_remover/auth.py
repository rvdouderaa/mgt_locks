"""
Azure authentication and client initialization
"""

import logging
from typing import Optional

from azure.core.exceptions import ClientAuthenticationError
from azure.identity import DefaultAzureCredential
from azure.mgmt.resource import ManagementLockClient

from .exceptions import AuthenticationError, AzureClientError


class AzureAuthManager:
    """Handles Azure authentication and client initialization."""

    def __init__(self, subscription_id: str):
        """
        Initialize the authentication manager.

        Args:
            subscription_id: Azure subscription ID
        """
        self.subscription_id = subscription_id
        self.logger = logging.getLogger(__name__)
        self._credential: Optional[DefaultAzureCredential] = None
        self._client: Optional[ManagementLockClient] = None

    @property
    def client(self) -> ManagementLockClient:
        """Get the initialized Management Lock client."""
        if self._client is None:
            self._initialize_client()
        if self._client is None:
            raise AzureClientError("Failed to initialize Azure client")
        return self._client

    def _initialize_client(self) -> None:
        """Initialize Azure Management Lock client with appropriate credentials."""
        try:
            # Use DefaultAzureCredential which handles multiple auth methods:
            # 1. Managed Identity (when running on Azure)
            # 2. Environment variables (service principal)
            # 3. Azure CLI (if logged in)
            # 4. Interactive browser (fallback)
            self._credential = DefaultAzureCredential()

            self._client = ManagementLockClient(
                credential=self._credential, subscription_id=self.subscription_id
            )

            self.logger.info(
                f"Initialized Azure client for subscription: {self.subscription_id}"
            )

        except ClientAuthenticationError as e:
            self.logger.error(f"Authentication failed: {e}")
            raise AuthenticationError(f"Failed to authenticate with Azure: {e}") from e
        except Exception as e:
            self.logger.error(f"Failed to initialize Azure client: {e}")
            raise AzureClientError(f"Failed to initialize Azure client: {e}") from e
