# Orientation

The `Orientation` class represents device orientation information with support for orientation change event handling.

## Dependencies

```python
from typing import Callable
from pyweber.utils.types import OrientationType
```

## Orientation Class

### Constructor
```python
def __init__(self, angle: int, type: OrientationType, on_change: Callable = None):
```

**Parameters:**
- `angle`: Orientation angle in degrees
- `type`: Orientation type from OrientationType enum
- `on_change`: Optional callback function for orientation changes

### Properties

#### `angle`
The current orientation angle in degrees.

#### `type`
The orientation type (from OrientationType enum).

#### `on_change` (Property with Setter)
Callback function that gets called when orientation changes.

**Getter:** Returns the current change handler function.

**Setter:** Sets the orientation change event handler.
- Accepts `None` to remove the handler
- Validates that the value is callable
- Raises `TypeError` if value is not callable

### Methods

The Orientation class primarily uses properties for data access and event handling.

## Usage Example

```python
from pyweber.models.window import Orientation
from pyweber.utils.types import OrientationType

# Define orientation change handler
def handle_orientation_change():
    print("Device orientation changed!")

# Create orientation instance
orientation = Orientation(
    angle=90,
    type=OrientationType.landscape,
    on_change=handle_orientation_change
)

# Access properties
print(orientation.angle)  # 90
print(orientation.type)   # OrientationType.landscape

# Update orientation change handler
def new_handler():
    print("New orientation detected!")

orientation.on_change = new_handler

# Remove orientation change handler
orientation.on_change = None
```

## Event Handling

### Setting Event Handlers
```python
# Method 1: During initialization
orientation = Orientation(
    angle=0,
    type=OrientationType.portrait,
    on_change=my_callback
)

# Method 2: Using property setter
orientation.on_change = my_callback

# Method 3: Remove handler
orientation.on_change = None
```

### Event Handler Requirements
- Must be a callable function
- Can accept no parameters (orientation data available through instance)
- Should handle orientation change logic

## Error Handling

### Type Validation
- `TypeError`: Raised when `on_change` is set to a non-callable value
- `None` values are accepted to remove event handlers

## Integration

The Orientation class is used by:
- `Screen` class for device screen orientation
- `Window` class for browser window orientation events
- Device orientation APIs for mobile web applications

## Common Use Cases

1. **Responsive Design**: Adjusting UI layout based on device orientation
2. **Game Development**: Handling device rotation in web games
3. **Media Applications**: Optimizing video/image display for orientation
4. **Mobile Web Apps**: Providing native-like orientation handling

## OrientationType Values

The orientation type typically includes values like:
- `portrait`: Device held vertically
- `landscape`: Device held horizontally
- `portrait-primary`: Primary portrait orientation
- `portrait-secondary`: Inverted portrait orientation
- `landscape-primary`: Primary landscape orientation
- `landscape-secondary`: Inverted landscape orientation

*Note: Exact values depend on the OrientationType enum implementation.*