# Azure Lock Remover - Code Architecture

## Overview

The Azure Lock Remover has been refactored from a single 400-line file into a modular, maintainable package with clear separation of concerns.

## File Structure

```
src/
├── main.py                              # Main entry point (87 lines)
├── main_old.py                          # Original single-file version (backup)
└── azure_lock_remover/                  # Main package
    ├── __init__.py                      # Package initialization (16 lines)
    ├── auth.py                          # Azure authentication (52 lines)
    ├── client.py                        # Main client class (40 lines)
    ├── exceptions.py                    # Custom exceptions (25 lines)
    ├── operations.py                    # Lock operations (150 lines)
    ├── parser.py                        # Lock scope parsing (90 lines)
    ├── retry.py                         # Retry logic (50 lines)
    └── utils.py                         # Utilities (28 lines)
```

## Module Responsibilities

### 1. `main.py` (87 lines)
**Purpose**: Entry point and CLI handling
- Command-line argument parsing
- Main execution flow
- Error handling and user feedback
- Minimal business logic

### 2. `azure_lock_remover/auth.py` (52 lines)
**Purpose**: Azure authentication and client management
- `AzureAuthManager` class
- DefaultAzureCredential handling
- Client initialization
- Authentication error handling

### 3. `azure_lock_remover/client.py` (40 lines)
**Purpose**: Main API interface
- `AzureLockRemover` class (facade pattern)
- Simple public interface
- Coordinates between other components

### 4. `azure_lock_remover/operations.py` (150 lines)
**Purpose**: Core lock management operations
- `LockOperations` class
- List locks functionality
- Remove individual/all locks
- Business logic for lock removal

### 5. `azure_lock_remover/parser.py` (90 lines)
**Purpose**: Lock scope parsing logic
- `LockScopeParser` class
- Resource group vs resource vs subscription scope detection
- Robust parsing with proper error handling
- Extraction of Azure resource identifiers

### 6. `azure_lock_remover/retry.py` (50 lines)
**Purpose**: Retry logic with exponential backoff
- `RetryManager` class
- Configurable retry attempts
- Exponential backoff algorithm
- Azure-specific transient error handling

### 7. `azure_lock_remover/exceptions.py` (25 lines)
**Purpose**: Custom exception hierarchy
- `LockRemovalError` (base)
- `AuthenticationError`
- `InvalidScopeError`
- `AzureClientError`
- `PermissionError`

### 8. `azure_lock_remover/utils.py` (28 lines)
**Purpose**: Shared utilities
- Logging configuration
- Subscription ID validation
- Common helper functions

## Benefits of Refactoring

### ✅ **Maintainability**
- Each module has a single responsibility
- Easy to locate and fix bugs
- Clear separation of concerns

### ✅ **Testability**
- Each component can be unit tested independently
- Mock dependencies easily
- Better test coverage

### ✅ **Reusability**
- Components can be reused in other projects
- `AzureLockRemover` class can be imported as a library
- Parser can be used standalone

### ✅ **Readability**
- Smaller, focused files
- Clear module purposes
- Better code organization

### ✅ **Extensibility**
- Easy to add new features
- Can extend authentication methods
- Can add new lock types or operations

## Key Design Patterns Used

### 1. **Facade Pattern**
`AzureLockRemover` provides a simple interface hiding complex subsystems.

### 2. **Single Responsibility Principle**
Each class/module has one reason to change.

### 3. **Dependency Injection**
Components accept dependencies rather than creating them.

### 4. **Strategy Pattern**
Different deletion strategies based on lock scope type.

### 5. **Error Handling Chain**
Structured exception hierarchy for different error types.

## Usage Examples

### As a CLI Tool
```bash
python src/main.py --subscription-id <sub-id> --dry-run
```

### As a Library
```python
from azure_lock_remover import AzureLockRemover

remover = AzureLockRemover(subscription_id="...", dry_run=True)
result = remover.remove_all_locks()
print(f"Processed {result['total']} locks")
```

### Individual Components
```python
from azure_lock_remover.auth import AzureAuthManager
from azure_lock_remover.parser import LockScopeParser

auth = AzureAuthManager("subscription-id")
parser = LockScopeParser()
scope_info = parser.parse_lock_scope("/subscriptions/.../resourcegroups/rg-name")
```

## Migration Notes

- **API Compatibility**: The main CLI interface remains identical
- **Functionality**: All original features preserved
- **Performance**: No performance impact, possibly slight improvement
- **Dependencies**: Same Azure SDK dependencies

## Future Enhancements Made Easy

With this modular structure, you can easily:
- Add support for new Azure authentication methods
- Implement different retry strategies
- Add lock filtering capabilities
- Support bulk operations from files
- Add progress bars or detailed reporting
- Implement lock backup/restore functionality

The refactored code maintains all the robustness and features of the original while providing a much more maintainable and extensible foundation.

## Architecture Flowchart

```mermaid
flowchart TD
    %% Entry Point
    CLI[main.py<br/>CLI Entry Point] --> ARG[Parse Arguments<br/>subscription-id, dry-run, log-level]
    
    %% Main Flow
    ARG --> CLIENT[AzureLockRemover<br/>Main Client/Facade]
    
    %% Authentication
    CLIENT --> AUTH[AzureAuthManager<br/>Handle Azure Auth]
    AUTH --> CRED[DefaultAzureCredential<br/>Azure SDK]
    AUTH --> MGMT[ManagementLockClient<br/>Azure SDK]
    
    %% Operations Flow
    CLIENT --> OPS[LockOperations<br/>Core Business Logic]
    
    %% List Locks Flow
    OPS --> LIST[list_all_locks]
    LIST --> SCOPE[Get Lock Scopes]
    SCOPE --> PARSER[LockScopeParser<br/>Parse Lock Scopes]
    
    %% Parser Logic
    PARSER --> PARSE_SUB[Subscription Lock?]
    PARSER --> PARSE_RG[Resource Group Lock?]
    PARSER --> PARSE_RES[Resource Lock?]
    
    PARSE_SUB --> SUB_INFO[type: subscription]
    PARSE_RG --> RG_INFO[type: resource_group<br/>resource_group_name]
    PARSE_RES --> RES_INFO[type: resource<br/>provider, resource_type<br/>resource_name, rg_name]
    
    %% Delete Flow
    OPS --> DELETE[delete_lock]
    DELETE --> RETRY[RetryManager<br/>Exponential Backoff]
    
    %% Retry Logic
    RETRY --> ATTEMPT[Attempt Delete]
    ATTEMPT --> SUCCESS[Success?]
    SUCCESS -->|Yes| DONE[Complete]
    SUCCESS -->|No| ERROR_CHECK[Retryable Error?]
    ERROR_CHECK -->|Yes| BACKOFF[Wait with Backoff]
    ERROR_CHECK -->|No| FAIL[Fail]
    BACKOFF --> ATTEMPT
    
    %% Different Delete Operations
    DELETE --> DEL_SUB[delete_at_subscription_level]
    DELETE --> DEL_RG[delete_at_resource_group_level]
    DELETE --> DEL_RES[delete_at_resource_level]
    
    %% Utilities and Support
    OPS --> UTILS[Utils<br/>Logging, Validation]
    OPS --> EXC[Custom Exceptions<br/>Error Handling]
    
    %% Dry Run Flow
    CLIENT --> DRY{Dry Run Mode?}
    DRY -->|Yes| LOG_ONLY[Log Only<br/>No Deletion]
    DRY -->|No| DELETE
    
    %% Error Handling
    AUTH --> AUTH_ERR[AuthenticationError]
    PARSER --> SCOPE_ERR[InvalidScopeError]
    DELETE --> CLIENT_ERR[AzureClientError]
    RETRY --> PERM_ERR[PermissionError]
    
    %% Styling
    classDef entryPoint fill:#e1f5fe
    classDef core fill:#f3e5f5
    classDef operations fill:#e8f5e8
    classDef external fill:#fff3e0
    classDef errors fill:#ffebee
    
    class CLI entryPoint
    class CLIENT,AUTH,OPS,PARSER,RETRY core
    class LIST,DELETE,PARSE_SUB,PARSE_RG,PARSE_RES operations
    class CRED,MGMT,DEL_SUB,DEL_RG,DEL_RES external
    class AUTH_ERR,SCOPE_ERR,CLIENT_ERR,PERM_ERR errors
```
