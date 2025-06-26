"""
Lock scope parsing utilities
"""

import logging
from typing import Dict, Any

from .exceptions import InvalidScopeError


class LockScopeParser:
    """Handles parsing of Azure management lock scopes."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def parse_lock_scope(self, lock_scope: str) -> Dict[str, Any]:
        """
        Parse a lock scope to determine its type and extract relevant information.

        Args:
            lock_scope: The lock scope string

        Returns:
            Dictionary containing scope type and parsed components

        Raises:
            InvalidScopeError: If the scope cannot be parsed
        """
        try:
            scope_lower = lock_scope.lower()

            if "/resourcegroups/" in scope_lower:
                return self._parse_resource_group_or_resource_scope(
                    lock_scope, scope_lower
                )
            else:
                return self._parse_subscription_scope(lock_scope)

        except Exception as e:
            self.logger.error(f"Failed to parse lock scope: {lock_scope}")
            raise InvalidScopeError(f"Invalid lock scope format: {lock_scope}") from e

    def _parse_resource_group_or_resource_scope(
        self, lock_scope: str, scope_lower: str
    ) -> Dict[str, Any]:
        """Parse resource group or resource-level lock scopes."""
        # Find the position of "resourcegroups" in the original scope
        rg_index = scope_lower.find("/resourcegroups/")
        if rg_index == -1:
            raise ValueError(f"Could not find resourcegroups in scope: {lock_scope}")

        # Extract everything after "/resourcegroups/"
        after_rg = lock_scope[rg_index + len("/resourcegroups/") :]

        if "/providers/" not in after_rg:
            # Resource group scoped lock
            # Format: /subscriptions/{sub-id}/resourcegroups/{rg-name}
            rg_name = after_rg.rstrip("/")  # Remove trailing slash if present
            return {"type": "resource_group", "resource_group_name": rg_name}
        else:
            # Resource scoped lock
            # Format: /subscriptions/{sub-id}/resourcegroups/{rg-name}/
            # providers/{provider}/{resource-type}/{resource-name}
            return self._parse_resource_scope(lock_scope, after_rg)

    def _parse_resource_scope(self, lock_scope: str, after_rg: str) -> Dict[str, Any]:
        """Parse resource-level lock scope."""
        # Need at least: rg-name, providers, provider-name, resource-type
        parts = after_rg.split("/")
        if len(parts) < 4:
            raise ValueError(f"Invalid resource lock scope format: {lock_scope}")

        rg_name = parts[0]

        # Find "providers" in the parts
        try:
            providers_index = next(
                i for i, part in enumerate(parts) if part.lower() == "providers"
            )
        except StopIteration:
            raise ValueError(f"Could not find providers in scope: {lock_scope}")

        if providers_index + 2 >= len(parts):
            raise ValueError(f"Invalid provider format in scope: {lock_scope}")

        provider = parts[providers_index + 1]
        resource_type = parts[providers_index + 2]

        # Resource name could be the next part or multiple parts combined
        if providers_index + 3 < len(parts):
            resource_name = "/".join(parts[providers_index + 3 :])
        else:
            raise ValueError(f"Could not find resource name in scope: {lock_scope}")

        return {
            "type": "resource",
            "resource_group_name": rg_name,
            "provider": provider,
            "resource_type": resource_type,
            "resource_name": resource_name,
        }

    def _parse_subscription_scope(self, lock_scope: str) -> Dict[str, Any]:
        """Parse subscription-level lock scope."""
        # Format: /subscriptions/{sub-id}
        return {"type": "subscription"}
