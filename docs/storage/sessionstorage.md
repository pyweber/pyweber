# SessionStorage

The `SessionStorage` class simulates browser sessionStorage functionality with automatic synchronization to connected WebSocket clients.

## Dependencies

```python
import asyncio
import json
from pyweber.utils.types import BaseStorage
from pyweber.connection.websocket import WebSocket
```

## SessionStorage Class

### Inheritance
```python
class SessionStorage(BaseStorage):
```

Inherits from `BaseStorage` for basic storage operations with JSON support.

### Constructor
```python
def __init__(self, data: dict[str, (int, float)], session_id: str, ws: 'WebSocket'):
```

**Parameters:**
- `data`: Initial storage data dictionary
- `session_id`: Session identifier for WebSocket communication
- `ws`: WebSocket connection instance for real-time updates

### Properties

#### Inherited from BaseStorage
- `data`: Raw storage data dictionary
- All BaseStorage methods: `get()`, `keys()`, `values()`, `items()`

#### SessionStorage Specific
- `session_id`: Session identifier for the storage instance
- `__ws`: Private WebSocket connection reference

### Methods

#### `set(key: str, value)`
Stores a value in sessionStorage and synchronizes with client.

**Parameters:**
- `key`: Storage key
- `value`: Value to store (automatically JSON-serialized if dict)

**Behavior:**
- Only stores non-empty values
- Automatically converts dict values to JSON strings
- Triggers real-time sync to client via WebSocket

#### `clear()`
Removes all items from sessionStorage and synchronizes with client.

**Behavior:**
- Clears all data from storage
- Triggers real-time sync to client via WebSocket

#### `pop(key: str)`
Removes and returns a value from sessionStorage.

**Parameters:**
- `key`: Storage key to remove

**Returns:**
- Raw value (no JSON deserialization unlike LocalStorage)
- None if key doesn't exist

**Behavior:**
- Only triggers sync if key existed and was removed
- Returns raw value without JSON parsing

## Usage Example

```python
from pyweber.models.window import SessionStorage
from pyweber.connection.websocket import WebSocket

# Initialize WebSocket connection
ws = WebSocket()
session_id = "user_session_123"

# Create sessionStorage instance
session_storage = SessionStorage(
    data={"current_page": "dashboard", "temp_data": "processing"},
    session_id=session_id,
    ws=ws
)

# Store simple values
session_storage.set("form_step", "2")
session_storage.set("temp_token", "abc123xyz")

# Store complex objects (auto JSON-serialized)
form_data = {
    "name": "John Doe",
    "email": "john@example.com",
    "step": 2
}
session_storage.set("form_data", form_data)

# Retrieve values
current_page = session_storage.get("current_page")  # "dashboard"
form_step = session_storage.get("form_step")        # "2"

# Note: Complex objects need manual JSON parsing when retrieved
form_data_raw = session_storage.get("form_data")    # JSON string
form_data_parsed = json.loads(form_data_raw)        # Parsed object

# Remove specific item
removed_token = session_storage.pop("temp_token")   # "abc123xyz"

# Get all keys and values
all_keys = session_storage.keys()     # ["current_page", "form_step", "form_data"]
all_values = session_storage.values() # ["dashboard", "2", "{"name": "John Doe"...}"]

# Clear all storage
session_storage.clear()
```

## Real-time Synchronization

### WebSocket Communication
SessionStorage automatically synchronizes changes with the client browser:

```python
# When data changes, sends message like:
{
    "sessionstorage": {
        "form_step": "2",
        "form_data": "{"name": "John Doe", "email": "john@example.com"}"
    }
}
```

### Async Handling
The `__send__()` method handles both sync and async contexts:
- Detects if running in async event loop
- Uses `asyncio.create_task()` if loop exists
- Falls back to `asyncio.run()` if no loop

## Differences from LocalStorage

### JSON Handling
- **LocalStorage**: Automatically deserializes JSON in `get()` and `pop()`
- **SessionStorage**: Returns raw values, requires manual JSON parsing

### Data Persistence
- **LocalStorage**: Persists across browser sessions
- **SessionStorage**: Only persists for the current session/tab

### Use Cases
- **LocalStorage**: Long-term user preferences, settings
- **SessionStorage**: Temporary data, form state, navigation state

## JSON Serialization

### Automatic Serialization
- Dict values are automatically converted to JSON strings in `set()`
- Other types are stored as-is
- Same behavior as LocalStorage

### Manual Deserialization Required
```python
# Storing complex data
session_storage.set("user_data", {"id": 123, "name": "John"})

# Retrieving requires manual parsing
raw_data = session_storage.get("user_data")  # JSON string
user_data = json.loads(raw_data)             # Parsed object
```

## Error Handling

### JSON Errors
- Serialization errors in `set()` should be handled by caller
- No automatic error handling for JSON operations
- Manual deserialization may raise `json.JSONDecodeError`

### WebSocket Errors
- WebSocket communication errors handled by WebSocket class
- SessionStorage assumes WebSocket is properly initialized

## Integration

SessionStorage integrates with:
- `Window` class for browser sessionStorage simulation
- `WebSocket` class for real-time client synchronization
- `BaseStorage` for core storage functionality
- Browser sessionStorage API through WebSocket messages

## Browser Compatibility

Simulates the standard sessionStorage API:
- `sessionStorage.setItem(key, value)` → `set(key, value)`
- `sessionStorage.getItem(key)` → `get(key)`
- `sessionStorage.removeItem(key)` → `pop(key)`
- `sessionStorage.clear()` → `clear()`
- `sessionStorage.key(index)` → `keys()[index]`

## Common Use Cases

1. **Form State**: Preserving form data during multi-step processes
2. **Navigation State**: Tracking current page, tab, or section
3. **Temporary Tokens**: Storing short-lived authentication tokens
4. **Wizard Progress**: Maintaining state in multi-step workflows
5. **Shopping Cart**: Temporary cart data for current session

## Performance Considerations

- Each `set()`, `clear()`, and successful `pop()` triggers WebSocket message
- Large objects are JSON-serialized on every storage operation
- Session data is cleared when browser tab/window closes
- Consider using for temporary data that doesn't need persistence

## Session Lifecycle

- Data persists only for the current browser session/tab
- Cleared when user closes the tab or browser
- Not shared between different tabs (unlike localStorage)
- Automatically cleared on session timeout