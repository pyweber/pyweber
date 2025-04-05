


# Window in PyWeber

The Window class in PyWeber provides an interface to interact with the browser window, offering access to browser properties, methods, and events.

## Window Properties

The Window object provides access to various browser properties:

```python
# Window dimensions
window.width          # Total window width
window.height         # Total window height
window.inner_width    # Viewport width
window.inner_height   # Viewport height

# Scroll position
window.scroll_x       # Horizontal scroll position
window.scroll_y       # Vertical scroll position

# Storage
window.local_storage  # Browser's localStorage
window.session_storage # Browser's sessionStorage
```

## Screen Information

The Window object provides access to screen properties through the `screen` property:

```python
# Screen properties
window.screen.width       # Screen width
window.screen.height      # Screen height
window.screen.colorDepth  # Color depth
window.screen.pixelDepth  # Pixel depth
window.screen.screenX     # X coordinate of window
window.screen.screenY     # Y coordinate of window

# Screen orientation
window.screen.orientation.angle  # Orientation angle in degrees
window.screen.orientation.type   # Orientation type (portrait/landscape)
```

## Location Information

The Window object provides access to location properties through the `location` property:

```python
# Location properties
window.location.host      # Host name and port
window.location.url       # Complete URL
window.location.origin    # Protocol, hostname and port
window.location.route     # Path portion of URL
window.location.protocol  # Protocol (http:, https:, etc.)
```

## Window Methods

The Window object provides methods to interact with the browser:

```python
# Dialog methods
window.alert("Message")                  # Display alert dialog
window.confirm("Are you sure?")          # Display confirmation dialog
window.prompt("Enter your name", "")     # Display prompt dialog

# Navigation methods
window.open("https://example.com")       # Open new window/tab
window.close()                           # Close current window

# Scrolling methods
window.scroll_to(0, 100)                 # Scroll to specific position
window.scroll_by(0, 50)                  # Scroll by offset

# Timing methods
window.set_timeout(callback, 1000)       # Execute after delay (ms)
window.set_interval(callback, 1000)      # Execute repeatedly (ms)
window.clear_timeout(timer_id)           # Cancel timeout
window.clear_interval(timer_id)          # Cancel interval

# Animation methods
window.request_animation_frame(callback) # Schedule before next repaint
window.cancel_animation_frame(frame_id)  # Cancel animation frame

# Encoding/decoding methods
window.btoa("Hello")                     # Encode to Base64
window.atob("SGVsbG8=")                  # Decode from Base64
```

## Window Events

The Window object supports various events through the `WindowEvents` class:

```python
from pyweber.utils.types import WindowEventType

# Register window events
window.events.onload = self.handle_load
window.events.onresize = self.handle_resize
window.events.onscroll = self.handle_scroll

# Using add_event method
window.add_event(WindowEventType.LOAD, self.handle_load)
window.add_event(WindowEventType.RESIZE, self.handle_resize)

# Remove events
window.remove_event(WindowEventType.SCROLL)
```

### Supported Window Events

PyWeber supports a comprehensive set of window events:

```python
# Window and navigation events
WindowEventType.LOAD              # onload - Window has loaded
WindowEventType.UNLOAD            # onunload - Window is unloading
WindowEventType.BEFORE_UNLOAD     # onbeforeunload - Before window unloads
WindowEventType.HASH_CHANGE       # onhashchange - URL hash has changed
WindowEventType.POP_STATE         # onpopstate - History state has changed
WindowEventType.DOM_CONTENT_LOADED # onDOMContentLoaded - DOM fully loaded

# Resize and visibility events
WindowEventType.RESIZE            # onresize - Window has been resized
WindowEventType.VISIBILITY_CHANGE # onvisibilitychange - Visibility changed

# Storage events
WindowEventType.STORAGE           # onstorage - Storage has changed

# Network events
WindowEventType.ONLINE            # ononline - Browser is online
WindowEventType.OFFLINE           # onoffline - Browser is offline
```

## Event Handling

Window event handlers receive an `EventHandler` object:

```python
async def handle_resize(self, e: pw.EventHandler):
    """Handle window resize event"""
    # Access window properties
    width = e.window.inner_width
    height = e.window.inner_height

    # Update responsive elements
    if width < 768:
        self.container.add_class("mobile")
        self.container.remove_class("desktop")
    else:
        self.container.add_class("desktop")
        self.container.remove_class("mobile")

    # Update the UI
    e.update()
```

## Example: Responsive Layout

```python
import pyweber as pw
from pyweber.utils.types import WindowEventType

class ResponsiveApp(pw.Template):
    def __init__(self, app: pw.Pyweber):
        super().__init__(template="index.html")
        self.app = app

        # Get container element
        self.container = self.querySelector(".container")

        # Set initial layout based on window size
        self.set_layout()

        # Register window resize event
        self.window.events.onresize = self.handle_resize

    def set_layout(self):
        """Set layout based on window size"""
        width = self.window.inner_width

        if width < 768:
            self.container.add_class("mobile")
            self.container.remove_class("desktop")
        else:
            self.container.add_class("desktop")
            self.container.remove_class("mobile")

    async def handle_resize(self, e: pw.EventHandler):
        """Handle window resize event"""
        self.set_layout()
        e.update()
```

## Example: Scroll-to-Top Button

```python
import pyweber as pw

class ScrollToTopApp(pw.Template):
    def __init__(self, app: pw.Pyweber):
        super().__init__(template="index.html")
        self.app = app

        # Create scroll-to-top button
        self.scroll_button = pw.Element(
            tag="button",
            id="scroll-top",
            content="↑",
            classes=["scroll-top-btn", "hidden"],
            events=pw.TemplateEvents(onclick=self.scroll_to_top)
        )

        # Add button to body
        body = self.querySelector("body")
        body.add_child(self.scroll_button)

        # Register scroll event
        self.window.events.onscroll = self.handle_scroll

    async def handle_scroll(self, e: pw.EventHandler):
        """Show/hide scroll button based on scroll position"""
        if e.window.scroll_y > 300:
            self.scroll_button.remove_class("hidden")
        else:
            self.scroll_button.add_class("hidden")
        e.update()

    async def scroll_to_top(self, e: pw.EventHandler):
        """Scroll to top of page"""
        e.window.scroll_to(0, 0)
        e.update()
```

## Example: Screen Orientation

```python
import pyweber as pw
from pyweber.utils.types import OrientationType

class OrientationApp(pw.Template):
    def __init__(self, app: pw.Pyweber):
        super().__init__(template="index.html")
        self.app = app

        # Get message element
        self.message = self.querySelector("#orientation-message")

        # Set initial message
        self.update_orientation_message()

        # Register orientation change event
        self.window.screen.orientation.on_change = self.handle_orientation_change

    def update_orientation_message(self):
        """Update message based on current orientation"""
        orientation = self.window.screen.orientation.type

        if orientation == OrientationType.PORTRAIT_PRIMARY:
            self.message.content = "You are in portrait mode"
        elif orientation == OrientationType.LANDSCAPE_PRIMARY:
            self.message.content = "You are in landscape mode"

    async def handle_orientation_change(self, e: pw.EventHandler):
        """Handle orientation change event"""
        self.update_orientation_message()
        e.update()
```

## Best Practices

1. **Use window events sparingly**: Too many window events can impact performance
2. **Debounce resize events**: Resize events fire rapidly, so debounce them
3. **Check browser compatibility**: Not all window methods are available in all browsers
4. **Handle errors gracefully**: Use try/except blocks for browser-specific features
5. **Update the UI**: Always call `e.update()` after making changes based on window events

## Next Steps
- Learn about [Template](template.md) in detail
- Explore [Routing](router.md) to connect templates to URLs
- Understand [Event Handling](events.md) for interactive applications