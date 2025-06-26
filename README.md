# Azure Subscription Lock Removal Tool

This Python tool removes all management locks from an Azure subscription using the Azure SDK for Python.

## Project Structure

The tool is built with a modular architecture for maintainability and extensibility:

```
src/
├── main.py                              # Main CLI entry point
└── azure_lock_remover/                  # Core package
    ├── __init__.py                      # Package exports
    ├── auth.py                          # Azure authentication
    ├── client.py                        # Main client interface
    ├── exceptions.py                    # Custom exceptions
    ├── operations.py                    # Lock operations
    ├── parser.py                        # Lock scope parsing
    ├── retry.py                         # Retry logic
    └── utils.py                         # Utilities
```

For detailed architecture information, see [ARCHITECTURE.md](ARCHITECTURE.md).

## Prerequisites

- Python 3.7 or higher
- Azure account with appropriate permissions
- Subscription ID of the target Azure subscription

## Installation

1. Install the required Python packages:
   ```bash
   pip install -r requirements.txt
   ```

   The script requires these Azure SDK packages:
   - `azure-mgmt-resource>=21.0.0` - Azure Resource Management client
   - `azure-identity>=1.12.0` - Azure authentication
   - `azure-core>=1.26.0` - Azure SDK core functionality

## Authentication

The script uses Azure DefaultAzureCredential which supports multiple authentication methods in order of preference:

1. **Managed Identity** (when running on Azure resources)
2. **Service Principal** via environment variables:
   ```bash
   export AZURE_CLIENT_ID="your-client-id"
   export AZURE_CLIENT_SECRET="your-client-secret"
   export AZURE_TENANT_ID="your-tenant-id"
   ```
3. **Azure CLI** (if you're logged in via `az login`)
4. **Interactive Browser** (fallback for local development)

## Required Permissions

Your Azure identity needs the following permissions on the target subscription:
- `Microsoft.Authorization/locks/read`
- `Microsoft.Authorization/locks/delete`

These permissions are included in the following built-in roles:
- **Owner**
- **Contributor** 
- **Custom role** with the above permissions

## Usage

### Basic Usage
```bash
python src/main.py --subscription-id 12345678-1234-1234-1234-123456789012
```

### Dry Run (List locks without removing them)
```bash
python src/main.py --subscription-id 12345678-1234-1234-1234-123456789012 --dry-run
```

### With Debug Logging
```bash
python src/main.py --subscription-id 12345678-1234-1234-1234-123456789012 --log-level DEBUG
```

## Command Line Arguments

- `--subscription-id` (required): Azure subscription ID in GUID format
- `--dry-run` (optional): List locks without removing them
- `--log-level` (optional): Logging level (DEBUG, INFO, WARNING, ERROR). Default: INFO

## Examples

1. **Remove all locks from a subscription:**
   ```bash
   python src/main.py --subscription-id 12345678-1234-1234-1234-123456789012
   ```

2. **Preview what locks would be removed:**
   ```bash
   python src/main.py --subscription-id 12345678-1234-1234-1234-123456789012 --dry-run
   ```

3. **Remove locks with detailed logging:**
   ```bash
   python src/main.py --subscription-id 12345678-1234-1234-1234-123456789012 --log-level DEBUG
   ```

## Features

- **Comprehensive lock removal**: Handles subscription, resource group, and resource-level locks
- **Retry logic**: Implements exponential backoff for transient failures
- **Dry run mode**: Preview operations without making changes
- **Detailed logging**: Configurable logging levels with timestamps
- **Error handling**: Graceful handling of authentication, permission, and network errors
- **Security**: Uses Azure best practices with DefaultAzureCredential

## Safety Features

- Subscription ID format validation
- Dry run mode for testing
- Detailed logging of all operations
- Graceful error handling
- Keyboard interrupt handling (Ctrl+C)

## Error Handling

The script handles various error scenarios:
- **Authentication failures**: Clear error messages for credential issues
- **Permission errors**: Specific handling for insufficient permissions (403 errors)
- **Network errors**: Retry logic with exponential backoff
- **Resource not found**: Graceful handling of already-removed locks
- **Invalid input**: Validation of subscription ID format

## Output

The script provides detailed output including:
- Number of locks found
- Progress updates for each lock being processed
- Success/failure counts
- Error details for failed operations
- Summary of operations performed

## Troubleshooting

### Authentication Issues
- Ensure you're logged in via `az login` or have appropriate environment variables set
- Verify your identity has the required permissions on the target subscription

### Permission Errors
- Check that your identity has `Microsoft.Authorization/locks/delete` permission
- Consider using a higher-privileged account like Owner or Contributor

### Network Issues
- The script includes retry logic for transient network failures
- Check your internet connection and Azure service status

### No Locks Found
- Verify the subscription ID is correct
- Ensure there are actually locks in the subscription
- Check that you have read permissions to see the locks

## Security Considerations

- The script follows Azure security best practices
- Uses managed identity when available
- Never hardcodes credentials
- Implements least privilege access patterns
- Provides audit trail through logging
