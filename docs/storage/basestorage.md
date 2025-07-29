# BaseStorage

The `BaseStorage` class provides a base implementation for browser storage mechanisms (localStorage and sessionStorage) with JSON serialization support.

## Dependencies

```python
import json
from typing import Any, Union, Dict
```

## BaseStorage Class

### Constructor
```python
def __init__(self, data: dict[str, (str, int)]):
```

**Parameters:**
- `data`: Dictionary containing storage data (defaults to empty dict if None)

### Properties

#### `data`
Raw storage data as a dictionary where values can be strings or integers.

### Methods

#### `get(key: str, /, default: Any = None) -> Union[Dict[str, Any], Any]`
Retrieves a value from storage with automatic JSON deserialization.

**Parameters:**
- `key`: Storage key to retrieve
- `default`: Default value if key doesn't exist

**Returns:** 
- Parsed JSON object if value is valid JSON
- Raw value if JSON parsing fails
- Default value if key doesn't exist

#### `keys()`
Returns a list of all storage keys.

**Returns:** List of string keys

#### `values()`
Returns a list of all storage values with JSON deserialization applied.

**Returns:** List of deserialized values

#### `items()`
Returns a list of key-value tuples with JSON deserialization applied.

**Returns:** List of (key, value) tuples

### Magic Methods

#### `__repr__()`
Returns a string representation of the filtered (JSON-parsed) data.

**Returns:** String representation of deserialized storage data

## Usage Example

```python
from pyweber.utils.types import BaseStorage

# Create storage with mixed data types
storage_data = {
    "user_id": "123",
    "preferences": '{"theme": "dark", "language": "en"}',
    "count": "42"
}

storage = BaseStorage(storage_data)

# Get values (automatic JSON parsing)
user_id = storage.get("user_id")           # "123"
preferences = storage.get("preferences")   # {"theme": "dark", "language": "en"}
count = storage.get("count")               # "42"
missing = storage.get("missing", "default") # "default"

# Get all keys, values, items
keys = storage.keys()     # ["user_id", "preferences", "count"]
values = storage.values() # ["123", {"theme": "dark", "language": "en"}, "42"]
items = storage.items()   # [("user_id", "123"), ("preferences", {...}), ...]

# String representation
print(storage)  # Shows deserialized data
```

## JSON Handling

The BaseStorage class automatically handles JSON serialization/deserialization:

### Automatic Deserialization
- `get()`, `values()`, and `items()` methods attempt to parse values as JSON
- Falls back to raw string value if JSON parsing fails
- Handles both `TypeError` and `json.JSONDecodeError`

### Data Filtering
The private `__filter_data()` method processes all storage data:
- Attempts to parse each value as JSON
- Returns original data if any parsing fails
- Used by `values()`, `items()`, and `__repr__()`

## Error Handling

### JSON Parsing Errors
- `TypeError`: Handled when value is not a string
- `json.JSONDecodeError`: Handled when value is not valid JSON
- Both errors result in returning the raw value

## Integration

BaseStorage serves as the foundation for:
- `LocalStorage` class for browser localStorage simulation
- `SessionStorage` class for browser sessionStorage simulation
- Any custom storage implementations requiring JSON handling

## Common Use Cases

1. **Browser Storage Simulation**: Base for localStorage/sessionStorage implementations
2. **Configuration Storage**: Storing and retrieving application settings
3. **Data Persistence**: Maintaining data across sessions with JSON support
4. **Type-Safe Storage**: Automatic conversion between JSON and Python objects