# Screen

The `Screen` class represents browser screen information including dimensions, color depth, position, and orientation details.

## Dependencies

```python
from pyweber.models.window import Orientation
```

## Screen Class

### Constructor
```python
def __init__(
    self,
    width: float,
    height: float,
    colorDepth: int,
    pixelDepth: int,
    screenX: float,
    screenY: float,
    orientation: Orientation
):
```

**Parameters:**
- `width`: Screen width in pixels
- `height`: Screen height in pixels
- `colorDepth`: Color depth in bits per pixel
- `pixelDepth`: Pixel depth in bits per pixel
- `screenX`: Horizontal position of the screen
- `screenY`: Vertical position of the screen
- `orientation`: Orientation object containing orientation details

### Properties

#### Display Dimensions
- `width`: Screen width in pixels (float)
- `height`: Screen height in pixels (float)

#### Color Information
- `colorDepth`: Number of bits used to represent colors
- `pixelDepth`: Number of bits used per pixel

#### Position Information
- `screenX`: Horizontal offset of the screen
- `screenY`: Vertical offset of the screen

#### Orientation
- `orientation`: Orientation object with angle, type, and change handler

## Usage Example

```python
from pyweber.models.window import Screen, Orientation
from pyweber.utils.types import OrientationType

# Create orientation
orientation = Orientation(
    angle=0,
    type=OrientationType.portrait,
    on_change=lambda: print("Orientation changed!")
)

# Create screen instance
screen = Screen(
    width=1920.0,
    height=1080.0,
    colorDepth=24,
    pixelDepth=24,
    screenX=0.0,
    screenY=0.0,
    orientation=orientation
)

# Access screen properties
print(f"Screen size: {screen.width}x{screen.height}")
print(f"Color depth: {screen.colorDepth} bits")
print(f"Pixel depth: {screen.pixelDepth} bits")
print(f"Position: ({screen.screenX}, {screen.screenY})")
print(f"Orientation: {screen.orientation.type} at {screen.orientation.angle}°")
```

## Screen Information Details

### Display Dimensions
- **width/height**: Physical or logical screen dimensions
- Typically represents the full screen resolution
- Values are in CSS pixels for web contexts

### Color and Pixel Depth
- **colorDepth**: Total bits available for color representation
  - Common values: 8, 16, 24, 32 bits
  - Higher values = more colors available
- **pixelDepth**: Bits used per pixel for display
  - Often same as colorDepth
  - May differ in some display configurations

### Screen Position
- **screenX/screenY**: Position of screen in multi-monitor setups
- (0, 0) typically represents the primary monitor
- Negative values possible for monitors positioned left/above primary

### Orientation Integration
The Screen class includes an Orientation object that provides:
- Current device/screen orientation angle
- Orientation type (portrait/landscape variants)
- Event handling for orientation changes

## Common Use Cases

1. **Responsive Design**: Adapting layouts based on screen size
2. **Multi-Monitor Support**: Handling different screen configurations
3. **Color Management**: Adjusting graphics based on color depth
4. **Device Detection**: Identifying device capabilities
5. **Orientation Handling**: Responding to device rotation

## Integration

The Screen class is used by:
- `Window` class for browser screen information
- Responsive design systems
- Device capability detection
- Graphics and media applications

## Browser Compatibility

Screen information typically maps to JavaScript's `screen` object properties:
- `screen.width` → `width`
- `screen.height` → `height`
- `screen.colorDepth` → `colorDepth`
- `screen.pixelDepth` → `pixelDepth`
- `screen.left` → `screenX`
- `screen.top` → `screenY`
- `screen.orientation` → `orientation`

## Example Screen Configurations

### Desktop Monitor
```python
desktop_screen = Screen(
    width=2560.0, height=1440.0,
    colorDepth=24, pixelDepth=24,
    screenX=0.0, screenY=0.0,
    orientation=landscape_orientation
)
```

### Mobile Device
```python
mobile_screen = Screen(
    width=375.0, height=812.0,
    colorDepth=24, pixelDepth=24,
    screenX=0.0, screenY=0.0,
    orientation=portrait_orientation
)
```

### Secondary Monitor
```python
secondary_screen = Screen(
    width=1920.0, height=1080.0,
    colorDepth=24, pixelDepth=24,
    screenX=2560.0, screenY=0.0,  # Positioned right of primary
    orientation=landscape_orientation
)
```