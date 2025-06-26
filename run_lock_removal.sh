#!/bin/bash

# Example usage script for the Azure Lock Removal Tool
# This script demonstrates how to use the lock removal tool

echo "🔓 Azure Subscription Lock Removal Tool"
echo "======================================="
echo ""

# Check if subscription ID is provided
if [ -z "$1" ]; then
    echo "❌ Error: Please provide a subscription ID"
    echo ""
    echo "Usage: $0 <subscription-id> [options]"
    echo ""
    echo "Examples:"
    echo "  $0 12345678-1234-1234-1234-123456789012"
    echo "  $0 12345678-1234-1234-1234-123456789012 --dry-run"
    echo "  $0 12345678-1234-1234-1234-123456789012 --log-level DEBUG"
    echo ""
    exit 1
fi

SUBSCRIPTION_ID="$1"
shift  # Remove first argument, keep the rest

# Check if Azure CLI is logged in
echo "🔍 Checking Azure CLI authentication..."
if ! az account show > /dev/null 2>&1; then
    echo "❌ Azure CLI is not logged in."
    echo "   Please run: az login"
    echo ""
    exit 1
fi

# Get current subscription info
CURRENT_SUB=$(az account show --query id -o tsv 2>/dev/null)
echo "✅ Azure CLI is authenticated"
echo "   Current subscription: $CURRENT_SUB"
echo ""

# Validate subscription ID format
if [[ ! "$SUBSCRIPTION_ID" =~ ^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$ ]]; then
    echo "❌ Error: Invalid subscription ID format"
    echo "   Expected format: 12345678-1234-1234-1234-123456789012"
    echo ""
    exit 1
fi

# Set the subscription if different from current
if [ "$CURRENT_SUB" != "$SUBSCRIPTION_ID" ]; then
    echo "🔄 Setting Azure CLI to target subscription: $SUBSCRIPTION_ID"
    if ! az account set --subscription "$SUBSCRIPTION_ID"; then
        echo "❌ Error: Failed to set subscription. Please check:"
        echo "   1. The subscription ID is correct"
        echo "   2. You have access to this subscription"
        echo ""
        exit 1
    fi
    echo "✅ Subscription set successfully"
    echo ""
fi

# Check permissions by trying to list locks
echo "🔐 Checking permissions..."
if az lock list --subscription "$SUBSCRIPTION_ID" > /dev/null 2>&1; then
    echo "✅ You have permission to read locks"
else
    echo "❌ Error: Insufficient permissions to read locks"
    echo "   Required permissions:"
    echo "   - Microsoft.Authorization/locks/read"
    echo "   - Microsoft.Authorization/locks/delete"
    echo ""
    exit 1
fi

# Show current locks
LOCK_COUNT=$(az lock list --subscription "$SUBSCRIPTION_ID" --query "length(@)" -o tsv 2>/dev/null || echo "0")
echo "📊 Found $LOCK_COUNT management locks in subscription $SUBSCRIPTION_ID"
echo ""

# Run the Python script
echo "🚀 Starting lock removal process..."
echo "   Command: python src/main.py --subscription-id $SUBSCRIPTION_ID $*"
echo ""

# Execute the Python script with all remaining arguments
python src/main.py --subscription-id "$SUBSCRIPTION_ID" "$@"

# Restore original subscription if it was changed
if [ "$CURRENT_SUB" != "$SUBSCRIPTION_ID" ]; then
    echo ""
    echo "🔄 Restoring original subscription: $CURRENT_SUB"
    az account set --subscription "$CURRENT_SUB"
fi

echo ""
echo "✅ Process completed!"
