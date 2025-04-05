# Events in PyWeber

Events are a core part of PyWeber's reactive programming model, allowing your applications to respond to user interactions in real-time.

## Event System Components

PyWeber's event system consists of four main components:

1. **EventData**: Contains information about the event (coordinates, key presses, etc.)
2. **EventHandler**: Provides context and methods for handling events
3. **TemplateEvents**: Holds event handlers for elements
4. **WindowEvents**: Holds event handlers for the browser window

## EventData

The `EventData` object contains information specific to the triggered event:
```python
# EventData properties
event_data.clientX    # X coordinate of mouse pointer
event_data.clientY    # Y coordinate of mouse pointer
event_data.key        # Key pressed (for keyboard events)
event_data.deltaX     # Horizontal scroll amount
event_data.deltaY     # Vertical scroll amount
event_data.touches    # Touch points (for touch events)
event_data.timestamp  # Time when the event occurred
```
## EventHandler

The `EventHandler` object is passed to every event handler function and provides context and methods:
```python
# EventHandler properties
e.event_type  # Type of event (e.g., "onclick")
e.route       # Current route path
e.element     # Element that triggered the event
e.template    # Template containing the element
e.window      # Browser window object
e.event_data  # Data specific to the event
e.app         # PyWeber application instance
e.session_id  # Current user session ID

# EventHandler methods
e.update()    # Update the UI after changes
e.reload()    # Reload the current page
```

## Registering Event Handlers

There are multiple ways to register event handlers:

### Method 1: During Element Creation
```python
import pyweber as pw

# Create button with click event
button = pw.Element(
    tag="button",
    content="Click Me",
    events=pw.TemplateEvents(
        onclick=self.handle_click,
        onmouseover=self.handle_hover
    )
)
```
### Method 2: Using Element.events Property
```python
# Get element from template
button = template.querySelector("#submit-button")

# Assign event handlers
button.events.onclick = self.handle_click
button.events.onmouseover = self.handle_hover
```

### Method 3: Using Element.add_event Method

```python
from pyweber.utils.types import EventType

# Add click event
button.add_event(EventType.CLICK, self.handle_click)

# Add hover event
button.add_event(EventType.MOUSEOVER, self.handle_hover)
```
## Event Handler Functions

Event handler functions receive an `EventHandler` object:
```python
async def handle_click(self, e: pw.EventHandler):
    """Handle click event on a button"""
    # Access the clicked element
    e.element.content = "Clicked!"

    # Access event data
    x, y = e.event_data.clientX, e.event_data.clientY
    print(f"Clicked at ({x}, {y})")

    # Update another element
    result = e.template.querySelector("#result")
    if result:
        result.content = "Button was clicked!"

    # Important: Update the UI
    e.update()
```

## Supported Event Types

PyWeber supports a comprehensive set of DOM events through the `EventType` enum:

### Element Events
```python
# Mouse events
EventType.CLICK       # onclick
EventType.DBLCLICK    # ondblclick
EventType.MOUSEDOWN   # onmousedown
EventType.MOUSEUP     # onmouseup
EventType.MOUSEMOVE   # onmousemove
EventType.MOUSEOVER   # onmouseover
EventType.MOUSEOUT    # onmouseout
EventType.MOUSEENTER  # onmouseenter
EventType.MOUSELEAVE  # onmouseleave
EventType.CONTEXTMENU # oncontextmenu
EventType.WHEEL       # onwheel

# Keyboard events
EventType.KEYDOWN     # onkeydown
EventType.KEYUP       # onkeyup
EventType.KEYPRESS    # onkeypress

# Form events
EventType.FOCUS       # onfocus
EventType.BLUR        # onblur
EventType.CHANGE      # onchange
EventType.INPUT       # oninput
EventType.SUBMIT      # onsubmit
EventType.RESET       # onreset
EventType.SELECT      # onselect

# Touch events (mobile)
EventType.TOUCHSTART  # ontouchstart
EventType.TOUCHMOVE   # ontouchmove
EventType.TOUCHEND    # ontouchend
EventType.TOUCHCANCEL # ontouchcancel
```

### Window Events
```python
# Window and navigation events
WindowEventType.LOAD              # onload
WindowEventType.UNLOAD            # onunload
WindowEventType.BEFORE_UNLOAD     # onbeforeunload
WindowEventType.HASH_CHANGE       # onhashchange
WindowEventType.POP_STATE         # onpopstate
WindowEventType.DOM_CONTENT_LOADED # onDOMContentLoaded

# Resize and visibility events
WindowEventType.RESIZE            # onresize
WindowEventType.VISIBILITY_CHANGE # onvisibilitychange
```

## Example: Clock with Events
```python
import pyweber as pw
from datetime import datetime
import asyncio

class Clock(pw.Template):
    def __init__(self, app: pw.Pyweber):
        super().__init__(template="index.html")
        self.app = app
        self.container = self.querySelector(".container")
        self.running = False

        # Create time display elements
        self.time_display = pw.Element(
            tag="div",
            classes=["time-display"],
            content="00:00:00"
        )

        # Create start/stop button
        self.toggle_button = pw.Element(
            tag="button",
            id="toggle",
            content="Start",
            events=pw.TemplateEvents(onclick=self.toggle_clock)
        )

        # Create reset button
        self.reset_button = pw.Element(
            tag="button",
            id="reset",
            content="Reset",
            events=pw.TemplateEvents(onclick=self.reset_clock)
        )

        # Add elements to container
        self.container.childs = [
            pw.Element(tag="h2", content="Clock"),
            self.time_display,
            pw.Element(
                tag="div",
                classes=["buttons"],
                childs=[self.toggle_button, self.reset_button]
            )
        ]

    async def toggle_clock(self, e: pw.EventHandler):
        self.running = not self.running
        self.toggle_button.content = "Stop" if self.running else "Start"

        if self.running:
            # Start the clock
            while self.running:
                now = datetime.now()
                self.time_display.content = now.strftime("%H:%M:%S")
                e.update()
                await asyncio.sleep(1)
        else:
            # Just update the UI to show the button change
            e.update()

    async def reset_clock(self, e: pw.EventHandler):
        self.running = False
        self.toggle_button.content = "Start"
        self.time_display.content = "00:00:00"
        e.update()
```

## Asynchronous Event Handling

PyWeber supports asynchronous event handlers using `async/await`:
```python
async def fetch_data(self, e: pw.EventHandler):
    # Show loading state
    e.element.content = "Loading..."
    e.update()

    # Simulate API call
    await asyncio.sleep(2)

    # Update UI with result
    e.element.content = "Data Loaded"
    e.update()
```

## Event Delegation

For dynamic content, use event delegation by attaching handlers to parent elements:
```python
class TodoList(pw.Template):
    def __init__(self, app):
        super().__init__(template="todo.html")

        self.todo_list = self.querySelector("#todo-list")
        self.add_button = self.querySelector("#add-todo")
        self.new_todo_input = self.querySelector("#new-todo")

        # Add event for the add button
        self.add_button.events.onclick = self.add_todo

        # Add event delegation for the entire list
        self.todo_list.events.onclick = self.handle_list_click

    async def add_todo(self, e: pw.EventHandler):
        todo_text = self.new_todo_input.value
        if todo_text:
            # Create new todo item with delete button
            todo_item = pw.Element(
                tag="li",
                classes=["todo-item"],
                content=todo_text,
                childs=[
                    pw.Element(
                        tag="button",
                        classes=["delete-btn"],
                        content="×"
                    )
                ]
            )

            # Add to list
            self.todo_list.add_child(todo_item)

            # Clear input
            self.new_todo_input.value = ""
            e.update()

    async def handle_list_click(self, e: pw.EventHandler):
        # Check if the clicked element is a delete button
        if "delete-btn" in e.element.classes:
            # Find the parent todo item
            todo_item = e.element.parent

            # Remove from list
            self.todo_list.remove_child(todo_item)
            e.update()
```

## Best Practices

1. **Always call e.update()**: After making changes to the DOM, call `e.update()` to refresh the UI
2. **Use async for long operations**: Make event handlers async for operations that take time
3. **Keep handlers focused**: Each handler should do one specific task
4. **Use event delegation**: For dynamic content, attach handlers to parent elements
5. **Validate user input**: Always validate form inputs before processing
6. **Handle errors gracefully**: Use try/except blocks to prevent crashes

## Next Steps

- Learn about [Elements](elements.md) for DOM manipulation
- Explore [Templates](template.md) for creating complete pages
- Understand [Pyweber](router.md) for handling navigation