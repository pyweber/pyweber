# Confirm

The `Confirm` class represents the result of a browser confirmation dialog, containing both the user's response and the dialog identifier.

## Confirm Class

### Constructor
```python
def __init__(self, confirm_result: str, confirm_id: str):
```

**Parameters:**
- `confirm_result`: User's response to the confirmation dialog
- `confirm_id`: Unique identifier for the confirmation dialog

### Properties

#### `result`
The user's response to the confirmation dialog.
- Typically "true" for OK/Yes or "false" for Cancel/No
- May contain other values depending on implementation

#### `id`
Unique identifier for the confirmation dialog.
- Used to match responses with specific confirmation requests
- Generated as UUID when dialog is created

### Magic Methods

#### `__repr__()`
Returns a string representation of the confirmation result.

**Format:** `result={result}, id={id}`

## Usage Example

```python
from pyweber.models.window import Confirm

# Create confirm result (typically done internally)
confirm_result = Confirm(
    confirm_result="true",
    confirm_id="550e8400-e29b-41d4-a716-446655440000"
)

# Access properties
print(confirm_result.result)  # "true"
print(confirm_result.id)      # "550e8400-e29b-41d4-a716-446655440000"

# String representation
print(confirm_result)         # result=true, id=550e8400-e29b-41d4-a716-446655440000

# Check user response
if confirm_result.result == "true":
    print("User confirmed the action")
else:
    print("User cancelled the action")
```

## Integration with Window

The Confirm class is typically used with the Window.confirm() method:

```python
# In an async context
async def handle_delete_request():
    # Show confirmation dialog
    confirm_result = await window.confirm("Are you sure you want to delete this item?")

    # Check user response
    if confirm_result.result == "true":
        # User confirmed - proceed with deletion
        delete_item()
        print(f"Item deleted (confirmation ID: {confirm_result.id})")
    else:
        # User cancelled - abort operation
        print(f"Deletion cancelled (confirmation ID: {confirm_result.id})")
```

## Result Values

### Standard Values
- `"true"`: User clicked OK, Yes, or Confirm
- `"false"`: User clicked Cancel, No, or closed dialog
- `"timeout"`: Dialog timed out without user response

### Custom Values
Depending on implementation, may include:
- `"ok"`, `"cancel"`, `"yes"`, `"no"`
- Custom button values for specialized dialogs

## Dialog Identification

### Purpose of ID
- Matches responses to specific confirmation requests
- Enables handling multiple simultaneous confirmations
- Provides audit trail for user interactions
- Useful for debugging and logging

### ID Generation
- Typically generated as UUID4 for uniqueness
- Created when confirmation dialog is initiated
- Passed to client and returned with response

## Error Handling

### Timeout Handling
```python
async def safe_confirm():
    try:
        result = await window.confirm("Proceed?", timeout=30)
        if result.result == "timeout":
            print("User didn't respond in time")
        else:
            print(f"User responded: {result.result}")
    except Exception as e:
        print(f"Confirmation failed: {e}")
```

### Validation
```python
def validate_confirm_result(confirm: Confirm):
    if not confirm.id:
        raise ValueError("Confirmation ID is required")

    if confirm.result not in ["true", "false", "timeout"]:
        print(f"Warning: Unexpected result value: {confirm.result}")
```

## Common Use Cases

1. **Delete Confirmations**: Confirming destructive operations
2. **Navigation Warnings**: Confirming page navigation with unsaved changes
3. **Action Verification**: Double-checking important user actions
4. **Data Loss Prevention**: Preventing accidental data loss
5. **Security Confirmations**: Verifying sensitive operations

## Browser Compatibility

Maps to JavaScript's `confirm()` dialog:
- `window.confirm("message")` returns boolean
- PyWeber extends this with ID tracking and async support
- Maintains familiar confirmation dialog UX

## Best Practices

### Message Design
```python
# Good: Clear, specific messages
await window.confirm("Delete this file permanently? This cannot be undone.")

# Avoid: Vague messages
await window.confirm("Are you sure?")
```

### Response Handling
```python
# Always check the result
confirm_result = await window.confirm("Save changes?")
if confirm_result.result == "true":
    save_changes()
elif confirm_result.result == "false":
    discard_changes()
else:
    handle_timeout_or_error()
```

### Timeout Management
```python
# Set appropriate timeouts for user context
quick_confirm = await window.confirm("Quick action?", timeout=10)
important_confirm = await window.confirm("Important decision?", timeout=60)
```