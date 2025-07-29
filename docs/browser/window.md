# Window

The `Window` class simulates browser window functionality, providing access to window properties, events, storage, and various browser APIs through WebSocket communication.

## Dependencies

```python
import asyncio
import base64
import json
from uuid import uuid4
from threading import Timer
from typing import Callable, Union, Literal
from pyweber.core.events import WindowEvents
from pyweber.connection.websocket import WebSocket
from pyweber.utils.types import WindowEventType, OrientationType, BaseStorage
```

## Window Class

### Constructor
```python
def __init__(self):
```

Initializes a new Window instance with default values and empty storage.

### Properties

#### Window Dimensions
- `width`: Outer window width (float)
- `height`: Outer window height (float)
- `inner_width`: Inner window width (float)
- `inner_height`: Inner window height (float)

#### Scroll Position
- `scroll_x`: Horizontal scroll position (float)
- `scroll_y`: Vertical scroll position (float)

#### Session and Connection
- `session_id`: Session identifier for WebSocket communication
- `__ws`: Private WebSocket connection instance

#### Browser Information
- `screen`: Screen object with display information
- `location`: Location object with URL information

#### Events and Storage
- `events`: WindowEvents instance for event handling
- `local_storage`: LocalStorage instance for persistent storage
- `session_storage`: SessionStorage instance for session storage

### Event Management

#### `get_event(event_id: str) -> Callable`
Retrieves an event handler by its ID.

**Parameters:**
- `event_id`: Event identifier

**Returns:** Event handler function or None

#### `get_all_event_ids` (Property)
Returns a list of all registered event IDs.

#### `add_event(event_type: WindowEventType, event: Callable)`
Adds an event handler for a specific event type.

**Parameters:**
- `event_type`: WindowEventType enum value
- `event`: Callable event handler function

**Raises:**
- `TypeError`: If event_type is not WindowEventType or event is not callable

#### `remove_event(event_type: WindowEventType)`
Removes an event handler for a specific event type.

**Parameters:**
- `event_type`: WindowEventType enum value

**Raises:**
- `TypeError`: If event_type is not WindowEventType

### Dialog Methods

#### `alert(message: str)`
Displays an alert dialog to the user.

**Parameters:**
- `message`: Alert message to display

#### `confirm(message: str, timeout: int = 300) -> Confirm` (async)
Displays a confirmation dialog and waits for user response.

**Parameters:**
- `message`: Confirmation message
- `timeout`: Timeout in seconds (default: 300)

**Returns:** Confirm object with user response and dialog ID

#### `prompt(message: str, default: str = "", timeout: int = 300) -> Prompt` (async)
Displays a prompt dialog for user input.

**Parameters:**
- `message`: Prompt message
- `default`: Default input value
- `timeout`: Timeout in seconds (default: 300)

**Returns:** Prompt object with user input and dialog ID

### Navigation Methods

#### `open(url: str, new_page: bool = False)`
Opens a URL in the current window or a new page.

**Parameters:**
- `url`: URL to open
- `new_page`: Whether to open in new page/tab

#### `close()`
Closes the current window (if opened by script).

### Scrolling Methods

#### `scroll_to(x: float = None, y: float = None, behavior: Literal['auto', 'smooth', 'instant'] = 'instant')`
Scrolls the window to a specific position.

**Parameters:**
- `x`: Horizontal position (uses current if None)
- `y`: Vertical position (uses current if None)
- `behavior`: Scroll behavior animation

#### `scroll_by(x: float = 0, y: float = 0, behavior: Literal['auto', 'smooth', 'instant'] = 'instant')`
Scrolls the window by a relative amount.

**Parameters:**
- `x`: Horizontal offset
- `y`: Vertical offset
- `behavior`: Scroll behavior animation

### Encoding Methods

#### `atob(encoded_string: str) -> str`
Decodes a Base64 encoded string.

**Parameters:**
- `encoded_string`: Base64 encoded string

**Returns:** Decoded UTF-8 string

#### `btoa(string: str) -> str`
Encodes a string to Base64.

**Parameters:**
- `string`: String to encode

**Returns:** Base64 encoded string

### Timer Methods (Not Implemented)

#### `set_timeout(callback: Callable, delay: int)`
**Status:** Not implemented - raises NotImplementedError

#### `set_interval(callback: Callable, interval: int)`
**Status:** Not implemented - raises NotImplementedError

#### `clear_timeout(timer: Timer)`
**Status:** Not implemented - raises NotImplementedError

#### `clear_interval(timer: Timer)`
**Status:** Not implemented - raises NotImplementedError

### Animation Methods (Not Implemented)

#### `request_animation_frame(callback: callable)`
**Status:** Not implemented - raises NotImplementedError

#### `cancel_animation_frame(frame_id)`
**Status:** Not implemented - raises NotImplementedError

### Magic Methods

#### `__repr__()`
Returns a string representation of the window.

**Format:** Shows width, height, inner dimensions, and scroll position

## Usage Examples

### Basic Window Operations
```python
from pyweber.models.window import window

# Access window properties
print(f"Window size: {window.width}x{window.height}")
print(f"Inner size: {window.inner_width}x{window.inner_height}")
print(f"Scroll position: ({window.scroll_x}, {window.scroll_y})")

# Show alert
window.alert("Welcome to the application!")

# Scroll operations
window.scroll_to(0, 100, behavior='smooth')
window.scroll_by(0, 50, behavior='instant')
```

### Async Dialog Operations
```python
async def user_interaction():
    # Get user confirmation
    confirm_result = await window.confirm("Do you want to save changes?")
    if confirm_result.result == "true":
        print("User confirmed save")

    # Get user input
    name_result = await window.prompt("Enter your name:", default="Anonymous")
    if name_result.result:
        print(f"User entered: {name_result.result}")

    # Navigation
    window.open("https://example.com", new_page=True)
```

### Event Handling
```python
from pyweber.utils.types import WindowEventType

# Define event handlers
def on_resize():
    print(f"Window resized to {window.width}x{window.height}")

def on_scroll():
    print(f"Scrolled to ({window.scroll_x}, {window.scroll_y})")

# Add event handlers
window.add_event(WindowEventType.RESIZE, on_resize)
window.add_event(WindowEventType.SCROLL, on_scroll)

# Remove event handler
window.remove_event(WindowEventType.RESIZE)
```

### Storage Operations
```python
# LocalStorage (persistent)
window.local_storage.set("theme", "dark")
window.local_storage.set("user_prefs", {"lang": "en", "notifications": True})

theme = window.local_storage.get("theme")  # "dark"
prefs = window.local_storage.get("user_prefs")  # {"lang": "en", "notifications": True}

# SessionStorage (temporary)
window.session_storage.set("current_tab", "dashboard")
window.session_storage.set("temp_data", {"step": 2, "form_id": "abc123"})

current_tab = window.session_storage.get("current_tab")  # "dashboard"
```

### Base64 Encoding/Decoding
```python
# Encode string to Base64
original = "Hello, World!"
encoded = window.btoa(original)  # "SGVsbG8sIFdvcmxkIQ=="

# Decode Base64 string
decoded = window.atob(encoded)   # "Hello, World!"
```

## WebSocket Integration

The Window class communicates with the browser through WebSocket messages:

### Message Format
```python
# Alert message
{"alert": "Message text"}

# Confirmation dialog
{"confirm": "Message text", "confirm_id": "uuid"}

# Prompt dialog
{"prompt": {"message": "Text", "default": "Default"}, "prompt_id": "uuid"}

# Navigation
{"open": {"path": "url", "new_page": false}}

# Scroll
{"scroll_to": {"x": 100, "y": 200, "behavior": "smooth"}}
```

### Async Communication
- Uses asyncio for non-blocking WebSocket communication
- Handles both sync and async contexts automatically
- Provides timeout support for user dialogs

## Browser Compatibility

Maps to standard browser Window API:
- `window.alert()` → `alert()`
- `window.confirm()` → `confirm()`
- `window.prompt()` → `prompt()`
- `window.open()` → `open()`
- `window.close()` → `close()`
- `window.scrollTo()` → `scroll_to()`
- `window.scrollBy()` → `scroll_by()`
- `window.atob()` → `atob()`
- `window.btoa()` → `btoa()`

## Global Instance

The module provides a pre-instantiated global window object:

```python
from pyweber.models.window import window

# Use the global window instance
window.alert("Hello!")
```

## Error Handling

### Event Management Errors
- `TypeError`: Raised for invalid event types or non-callable handlers

### WebSocket Errors
- Handled internally by WebSocket class
- Automatic fallback between async and sync contexts

### Dialog Timeouts
- Configurable timeout for confirm/prompt dialogs
- Returns appropriate timeout indicators

## Common Use Cases

1. **User Interaction**: Alerts, confirmations, and input prompts
2. **Navigation**: Opening URLs and managing page flow
3. **Data Storage**: Persistent and session-based storage
4. **Event Handling**: Responding to window events
5. **Scrolling**: Programmatic scroll control
6. **Data Encoding**: Base64 encoding/decoding operations

## Performance Considerations

- Each operation triggers WebSocket communication
- Async methods should be awaited properly
- Storage operations sync with client in real-time
- Event handlers are called synchronously

## Security Notes

- Base64 encoding is not encryption
- Validate all user input from prompts
- Storage data is transmitted over WebSocket
- Dialog timeouts prevent indefinite blocking