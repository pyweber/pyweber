# LocalStorage

The `LocalStorage` class simulates browser localStorage functionality with automatic synchronization to connected WebSocket clients.

## Dependencies

```python
import asyncio
import json
from pyweber.utils.types import BaseStorage
from pyweber.connection.websocket import WebSocket
```

## LocalStorage Class

### Inheritance
```python
class LocalStorage(BaseStorage):
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

#### LocalStorage Specific
- `session_id`: Session identifier for the storage instance
- `__ws`: Private WebSocket connection reference

### Methods

#### `set(key: str, value)`
Stores a value in localStorage and synchronizes with client.

**Parameters:**
- `key`: Storage key
- `value`: Value to store (automatically JSON-serialized if dict)

**Behavior:**
- Only stores non-empty values
- Automatically converts dict values to JSON strings
- Triggers real-time sync to client via WebSocket

#### `clear()`
Removes all items from localStorage and synchronizes with client.

**Behavior:**
- Clears all data from storage
- Triggers real-time sync to client via WebSocket

#### `pop(key: str)`
Removes and returns a value from localStorage.

**Parameters:**
- `key`: Storage key to remove

**Returns:**
- Parsed JSON object if value was valid JSON
- Raw value if JSON parsing fails
- None if key doesn't exist

**Behavior:**
- Only triggers sync if key existed and was removed
- Attempts JSON deserialization on returned value

## Usage Example

```python
from pyweber.models.window import LocalStorage
from pyweber.connection.websocket import WebSocket

# Initialize WebSocket connection
ws = WebSocket()
session_id = "user_session_123"

# Create localStorage instance
local_storage = LocalStorage(
    data={"theme": "dark", "user_id": "456"},
    session_id=session_id,
    ws=ws
)

# Store simple values
local_storage.set("username", "john_doe")
local_storage.set("last_login", "2024-01-15")

# Store complex objects (auto JSON-serialized)
user_preferences = {
    "language": "en",
    "notifications": True,
    "theme": "dark"
}
local_storage.set("preferences", user_preferences)

# Retrieve values (auto JSON-deserialized)
username = local_storage.get("username")        # "john_doe"
preferences = local_storage.get("preferences")  # {"language": "en", ...}

# Remove specific item
removed_theme = local_storage.pop("theme")      # "dark"

# Get all keys and values
all_keys = local_storage.keys()     # ["username", "last_login", "preferences"]
all_values = local_storage.values() # ["john_doe", "2024-01-15", {...}]

# Clear all storage
local_storage.clear()
```

## Real-time Synchronization

### WebSocket Communication
LocalStorage automatically synchronizes changes with the client browser:

```python
# When data changes, sends message like:
{
    "localstorage": {
        "username": "john_doe",
        "preferences": "{"language": "en", "notifications": true}"
    }
}
```

### Async Handling
The `__send__()` method handles both sync and async contexts:
- Detects if running in async event loop
- Uses `asyncio.create_task()` if loop exists
- Falls back to `asyncio.run()` if no loop

## JSON Serialization

### Automatic Serialization
- Dict values are automatically converted to JSON strings
- Other types are stored as-is
- Serialization happens in `set()` method

### Automatic Deserialization
- `get()` and `pop()` methods attempt JSON parsing
- Falls back to raw value if parsing fails
- Inherited from BaseStorage functionality

## Error Handling

### JSON Errors
- `TypeError` and `json.JSONDecodeError` are caught and handled
- Failed parsing returns the raw string value
- No exceptions propagated to user code

### WebSocket Errors
- WebSocket communication errors should be handled by the WebSocket class
- LocalStorage assumes WebSocket is properly initialized

## Integration

LocalStorage integrates with:
- `Window` class for browser localStorage simulation
- `WebSocket` class for real-time client synchronization
- `BaseStorage` for core storage functionality
- Browser localStorage API through WebSocket messages

## Browser Compatibility

Simulates the standard localStorage API:
- `localStorage.setItem(key, value)` → `set(key, value)`
- `localStorage.getItem(key)` → `get(key)`
- `localStorage.removeItem(key)` → `pop(key)`
- `localStorage.clear()` → `clear()`
- `localStorage.key(index)` → `keys()[index]`

## Common Use Cases

1. **User Preferences**: Storing theme, language, layout preferences
2. **Session Data**: Maintaining user state across page reloads
3. **Form Data**: Preserving form inputs during navigation
4. **Cache Management**: Storing frequently accessed data
5. **Offline Support**: Maintaining data when connection is lost

## Performance Considerations

- Each `set()`, `clear()`, and successful `pop()` triggers WebSocket message
- Large objects are JSON-serialized on every storage operation
- Consider batching multiple changes when possible
- WebSocket message size affects network performance