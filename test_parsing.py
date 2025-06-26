#!/usr/bin/env python3
"""
Test script to verify the lock scope parsing logic
"""


def test_lock_scope_parsing():
    """Test the improved lock scope parsing logic"""

    # Test cases from your actual environment
    test_scopes = [
        "/subscriptions/5f417fb1-5f3a-4f2d-84b7-1b7850330b5f/resourcegroups/rg-cognos-monitoring-t-weu-01",
        "/subscriptions/5f417fb1-5f3a-4f2d-84b7-1b7850330b5f/resourcegroups/rg-cognos-bastion-t-weu-01",
        "/subscriptions/5f417fb1-5f3a-4f2d-84b7-1b7850330b5f/resourcegroups/DfcDataExportRG",
        "/subscriptions/5f417fb1-5f3a-4f2d-84b7-1b7850330b5f/resourcegroups/rg-cognos-backup-t-weu-01",
        "/subscriptions/5f417fb1-5f3a-4f2d-84b7-1b7850330b5f/resourcegroups/rg-test/providers/Microsoft.Storage/storageAccounts/mystorageaccount",
    ]

    for lock_scope in test_scopes:
        print(f"\nTesting scope: {lock_scope}")

        scope_lower = lock_scope.lower()

        if "/resourcegroups/" in scope_lower:
            # Find the position of "resourcegroups" in the original scope
            rg_index = scope_lower.find("/resourcegroups/")
            if rg_index == -1:
                print(f"  ERROR: Could not find resourcegroups in scope")
                continue

            # Extract everything after "/resourcegroups/"
            after_rg = lock_scope[rg_index + len("/resourcegroups/") :]
            print(f"  after_rg: '{after_rg}'")

            if "/providers/" not in after_rg:
                # Resource group scoped lock
                rg_name = after_rg.rstrip("/")  # Remove trailing slash if present
                print(f"  ✅ Resource Group Lock - RG: '{rg_name}'")
            else:
                # Resource scoped lock
                parts = after_rg.split("/")
                print(f"  parts: {parts}")

                if (
                    len(parts) < 4
                ):  # Need at least: rg-name, providers, provider-name, resource-type
                    print(f"  ERROR: Invalid resource lock scope format")
                    continue

                rg_name = parts[0]

                # Find "providers" in the parts
                try:
                    providers_index = next(
                        i for i, part in enumerate(parts) if part.lower() == "providers"
                    )
                    print(f"  providers_index: {providers_index}")
                except StopIteration:
                    print(f"  ERROR: Could not find providers in scope")
                    continue

                if providers_index + 2 >= len(parts):
                    print(f"  ERROR: Invalid provider format in scope")
                    continue

                provider = parts[providers_index + 1]
                resource_type = parts[providers_index + 2]

                # Resource name could be the next part or multiple parts combined
                if providers_index + 3 < len(parts):
                    resource_name = "/".join(parts[providers_index + 3 :])
                else:
                    print(f"  ERROR: Could not find resource name in scope")
                    continue

                print(
                    f"  ✅ Resource Lock - RG: '{rg_name}', Provider: '{provider}', Type: '{resource_type}', Name: '{resource_name}'"
                )
        else:
            # Subscription scoped lock
            print(f"  ✅ Subscription Lock")


if __name__ == "__main__":
    test_lock_scope_parsing()
