
# Event Handling in PyWeber

PyWeber provides a robust event handling system that allows your web applications to respond to user interactions in real-time. This document explains how events work in PyWeber and how to use them effectively.

## Event System Overview

The event system in PyWeber consists of three main components:

1. **EventType**: An enumeration of all supported event types
2. **Events**: A class that holds event handler functions
3. **EventHandler**: An object passed to event handlers with event information
4. **EventData**: Contains data specific to the triggered event

## Registering Event Handlers

There are multiple ways to register event handlers in PyWeber:

### Method 1: Using Element.events Property

```python
# Get an element from the template
button = template.querySelector("#submit-button")

# Assign event handlers
button.events.onclick = handle_click
button.events.onmouseover = handle_hover
```

### Method 2: Using Element.add_event Method

```python
from pyweber.utils.types import EventType

# Add click event
button.add_event(EventType.CLICK, handle_click)

# Add hover event
button.add_event(EventType.MOUSEOVER, handle_hover)
```

### Method 3: During Element Creation

```python
from pyweber import Element
from pyweber.utils.types import Events

# Create element with events
button = Element(
    name="button",
    content="Click Me",
    events=Events(
        onclick=handle_click,
        onmouseover=handle_hover
    )
)
```

## Event Handler Functions

Event handler functions receive an `EventHandler` object that contains information about the event:

```python
def handle_click(e: EventHandler):
    """Handle click event on a button"""
    # e.element - The element that triggered the event
    # e.template - The template containing the element
    # e.event_type - The type of event (e.g., "onclick")
    # e.route - The current route path
    # e.event_data - Data specific to the event

    # Example: Change the button text
    e.element.content = "Clicked!"

    # Example: Update another element
    result = e.template.querySelector("#result")
    if result:
        result.content = "Button was clicked!"
```

## EventHandler Object

The `EventHandler` object is passed to every event handler function and contains the following properties:

| Property | Type | Description |
|----------|------|-------------|
| `event_type` | str | The type of event (e.g., "onclick") |
| `route` | str | The current route path |
| `element` | Element | The element that triggered the event |
| `template` | Template | The template containing the element |
| `event_data` | EventData | Data specific to the event |

## EventData Object

The `EventData` object contains information specific to the triggered event:

| Property | Type | Description |
|----------|------|-------------|
| `clientX` | int | X coordinate of the mouse pointer |
| `clientY` | int | Y coordinate of the mouse pointer |
| `key` | str | Key pressed (for keyboard events) |
| `deltaX` | int | Horizontal scroll amount |
| `deltaY` | int | Vertical scroll amount |
| `touches` | list | Touch points (for touch events) |
| `timestamp` | int | Time when the event occurred |

## Supported Event Types

PyWeber supports a comprehensive set of DOM events through the `EventType` enum:

### Mouse Events

```python
from pyweber.utils.types import EventType

# Mouse events
EventType.CLICK       # onclick - Element is clicked
EventType.DBLCLICK    # ondblclick - Element is double-clicked
EventType.MOUSEDOWN   # onmousedown - Mouse button is pressed
EventType.MOUSEUP     # onmouseup - Mouse button is released
EventType.MOUSEMOVE   # onmousemove - Mouse is moved over element
EventType.MOUSEOVER   # onmouseover - Mouse enters element
EventType.MOUSEOUT    # onmouseout - Mouse leaves element
EventType.MOUSEENTER  # onmouseenter - Mouse enters (no bubbling)
EventType.MOUSELEAVE  # onmouseleave - Mouse leaves (no bubbling)
EventType.CONTEXTMENU # oncontextmenu - Right-click on element
EventType.WHEEL       # onwheel - Mouse wheel is rotated
```

### Keyboard Events

```python
# Keyboard events
EventType.KEYDOWN     # onkeydown - Key is pressed
EventType.KEYUP       # onkeyup - Key is released
EventType.KEYPRESS    # onkeypress - Key is pressed and released
```

### Form Events

```python
# Form events
EventType.FOCUS       # onfocus - Element receives focus
EventType.BLUR        # onblur - Element loses focus
EventType.CHANGE      # onchange - Element value changes
EventType.INPUT       # oninput - Input value changes
EventType.SUBMIT      # onsubmit - Form is submitted
EventType.RESET       # onreset - Form is reset
EventType.SELECT      # onselect - Text is selected
```

### Drag & Drop Events

```python
# Drag & Drop events
EventType.DRAG        # ondrag - Element is being dragged
EventType.DRAGSTART   # ondragstart - Drag operation starts
EventType.DRAGEND     # ondragend - Drag operation ends
EventType.DRAGOVER    # ondragover - Element is dragged over target
EventType.DRAGENTER   # ondragenter - Element enters drop target
EventType.DRAGLEAVE   # ondragleave - Element leaves drop target
EventType.DROP        # ondrop - Element is dropped on target
```

### Scroll & Resize Events

```python
# Scroll & Resize events
EventType.SCROLL      # onscroll - Element's scroll position changes
EventType.RESIZE      # onresize - Element is resized
```

### Media Events

```python
# Media events
EventType.PLAY        # onplay - Media starts playing
EventType.PAUSE       # onpause - Media is paused
EventType.ENDED       # onended - Media playback completes
EventType.VOLUMECHANGE # onvolumechange - Media volume changes
EventType.SEEKED      # onseeked - Media seeking completes
EventType.SEEKING     # onseeking - Media seeking starts
EventType.TIMEUPDATE  # ontimeupdate - Playback position changes
```

### Network Events

```python
# Network events
EventType.ONLINE      # ononline - Browser goes online
EventType.OFFLINE     # onoffline - Browser goes offline
```

### Touch Events (Mobile)

```python
# Touch events
EventType.TOUCHSTART  # ontouchstart - Touch begins on element
EventType.TOUCHMOVE   # ontouchmove - Touch moves on element
EventType.TOUCHEND    # ontouchend - Touch ends on element
EventType.TOUCHCANCEL # ontouchcancel - Touch is interrupted
```

## Removing Event Handlers

You can remove event handlers using the `remove_event` method:

```python
# Remove a specific event handler
button.remove_event(EventType.CLICK)

# Reset all event handlers
button.events = Events()
```

## Event Propagation

PyWeber implements standard DOM event propagation with capturing and bubbling phases:

1. **Capturing Phase**: Events travel from the root to the target element
2. **Target Phase**: Event reaches the target element
3. **Bubbling Phase**: Events bubble up from the target to the root

## Example: Complete Event Handling

```python
from pyweber import Template, Element
from pyweber.utils.types import EventType
from pyweber.utils.events import EventHandler

class Counter(Template):
    def __init__(self, app):
        super().__init__(template="counter.html")

        # Initialize counter
        self.count = 0

        # Get elements
        self.counter_display = self.querySelector("#counter")
        self.increment_btn = self.querySelector("#increment")
        self.decrement_btn = self.querySelector("#decrement")
        self.reset_btn = self.querySelector("#reset")

        # Set initial value
        self.counter_display.content = str(self.count)

        # Add event handlers
        self.increment_btn.events.onclick = self.increment
        self.decrement_btn.events.onclick = self.decrement
        self.reset_btn.events.onclick = self.reset

        # Add keyboard support
        self.add_event(EventType.KEYDOWN, self.handle_keydown)

    def increment(self, e: EventHandler):
        self.count += 1
        self.update_display()

        # Access event data
        x, y = e.event_data.clientX, e.event_data.clientY
        print(f"Increment clicked at position ({x}, {y})")

    def decrement(self, e: EventHandler):
        self.count -= 1
        self.update_display()

    def reset(self, e: EventHandler):
        self.count = 0
        self.update_display()

    def handle_keydown(self, e: EventHandler):
        key = e.event_data.key

        if key == "ArrowUp":
            self.increment(e)
        elif key == "ArrowDown":
            self.decrement(e)
        elif key == "r":
            self.reset(e)

    def update_display(self):
        self.counter_display.content = str(self.count)
```

## Event Delegation

For dynamic content or performance optimization, you can use event delegation by attaching event handlers to parent elements:

```python
class TodoList(Template):
    def __init__(self, app):
        super().__init__(template="todo.html")

        self.todo_list = self.querySelector("#todo-list")
        self.add_button = self.querySelector("#add-todo")
        self.new_todo_input = self.querySelector("#new-todo")

        # Add event for the add button
        self.add_button.events.onclick = self.add_todo

        # Add event delegation for the entire list
        self.todo_list.events.onclick = self.handle_list_click

    def add_todo(self, e: EventHandler):
        todo_text = self.new_todo_input.value
        if todo_text:
            # Create new todo item
            todo_item = Element(
                name="li",
                classes=["todo-item"],
                content=todo_text
            )

            # Add delete button
            delete_btn = Element(
                name="button",
                classes=["delete-btn"],
                content="×"
            )
            todo_item.childs.append(delete_btn)

            # Add to list
            self.todo_list.childs.append(todo_item)

            # Clear input
            self.new_todo_input.value = ""

    def handle_list_click(self, e: EventHandler):
        # Check if the clicked element is a delete button
        clicked = e.element

        if "delete-btn" in clicked.classes:
            # Find the parent todo item
            todo_item = clicked.parent

            # Remove from list
            self.todo_list.childs.remove(todo_item)
```

## Custom Events

PyWeber also supports creating and dispatching custom events:

```python
from pyweber.utils.events import EventData, EventHandler

class CustomEventExample(Template):
    def __init__(self, app):
        super().__init__(template="custom_events.html")

        self.button = self.querySelector("#trigger-button")
        self.result = self.querySelector("#result")

        # Regular click event
        self.button.events.onclick = self.trigger_custom_event

    def trigger_custom_event(self, e: EventHandler):
        # Create custom event data
        custom_data = {
            'timestamp': 1234567890,
            'clientX': 100,
            'clientY': 200,
            'custom_field': 'custom_value'
        }

        # Create event data
        event_data = EventData(custom_data)

        # Create event handler
        custom_event = EventHandler(
            event_type="custom_event",
            route=e.route,
            element=self.result,
            template=e.template,
            event_data=event_data
        )

        # Handle the custom event
        self.handle_custom_event(custom_event)

    def handle_custom_event(self, e: EventHandler):
        # Process the custom event
        self.result.content = f"Custom event triggered at {e.event_data.timestamp}"
```

## Best Practices

1. **Use Descriptive Handler Names**: Name event handlers clearly to indicate their purpose.

2. **Keep Handlers Focused**: Each handler should do one thing well.

3. **Avoid DOM Manipulation in Loops**: Batch DOM changes for better performance.

4. **Use Event Delegation**: For dynamic content, attach handlers to parent elements.

5. **Clean Up Event Listeners**: Remove event listeners when they're no longer needed.

6. **Validate User Input**: Always validate form inputs before processing.

7. **Prevent Default When Needed**: For form submissions or link clicks that should be handled by your code.

8. **Error Handling**: Wrap event handler code in try/except blocks to prevent crashes.

## Next Steps

- Learn about [Elements](elements.md) for DOM manipulation
- Explore [Templates](template.md) for creating complete pages
- Understand [Router](router.md) for handling navigation