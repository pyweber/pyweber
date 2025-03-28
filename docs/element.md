
# Elements in PyWeber

Elements are the building blocks of PyWeber templates. They represent HTML elements and provide an object-oriented way to manipulate the DOM.

## Element Class

The `Element` class is the core component for DOM manipulation in PyWeber. It represents an HTML element with properties, attributes, and event handlers.

### Creating Elements

Elements are typically created when parsing an HTML template, but you can also create them programmatically:

```python
from pyweber import Element
from pyweber.utils.types import Events, EventType

# Create a basic element
button = Element(
    tag="button",
    id="submit-btn",
    classes=["btn", "btn-primary"],
    content="Submit",
    attrs={"type": "submit"}
)

# Create a nested structure
form = Element(
    tag="form",
    id="contact-form",
    childs=[
        Element(tag="input", attrs={"type": "text", "name": "name"}),
        Element(tag="input", attrs={"type": "email", "name": "email"}),
        button
    ]
)
```
### Element Properties

| Property | Type | Description |
|----------|------|-------------|
| `name` | str | HTML tag name (e.g., "div", "button") |
| `id` | str | Element ID attribute |
| `classes` | list[str] | Element class attribute |
| `content` | str | Text content of the element |
| `value` | str | Value attribute (for form elements) |
| `attrs` | dict[str, str] | Additional HTML attributes |
| `parent` | Element | Parent element |
| `childs` | list[Element] | Child elements |
| `uuid` | str | Unique identifier (auto-generated) |
| `events` | Events | Event handlers attached to the element |

### Working with Elements

#### Modifying Properties
```python
# Change element properties
element.id = "new-id"
element.add_class("new-class")
element.content = "New content"
element.value = "New value"

# Add or modify attributes
element.attrs["data-custom"] = "value"
element.attrs["aria-label"] = "Description"
```

#### Managing Child Elements
```python
# Add a child element
new_child = Element(tag="span", content="Child text")
parent_element.childs.append(new_child)
new_child.parent = parent_element

# Remove a child element
parent_element.childs.remove(child_element)

## Event Handling

PyWeber provides a comprehensive event system for handling user interactions.

### Adding Event Listeners

from pyweber.utils.types import EventType

# Method 1: Using add_event method
element.add_event(EventType.CLICK, handle_click)

# Method 2: Using events property
element.events.onclick = handle_click
element.events.onsubmit = handle_submit
```
### Event Handler Functions

Event handlers receive an `EventHandler` object with information about the event:
```python
def handle_click(e: EventHandler):
    # Access the clicked element
    clicked = e.element

    # Access event data
    x, y = e.event_data.clientX, e.event_data.clientY

    # Access the template
    template = e.template

    # Modify the DOM in response to the event
    clicked.content = "Clicked!"

    # Find and update other elements
    result = template.querySelector("#result")
    if result:
        result.content = f"Clicked at ({x}, {y})"
```

### Removing Event Listeners
```python
# Remove a specific event listener
element.remove_event(EventType.CLICK)

# Reset all event listeners by creating a new Events object
element.events = Events()
```
## Available Events

PyWeber supports a wide range of standard DOM events:

### Mouse Events
- `onclick` - Element is clicked
- `ondblclick` - Element is double-clicked
- `onmousedown` - Mouse button is pressed on element
- `onmouseup` - Mouse button is released on element
- `onmousemove` - Mouse is moved over element
- `onmouseover` - Mouse enters element
- `onmouseout` - Mouse leaves element
- `onmouseenter` - Mouse enters element (no bubbling)
- `onmouseleave` - Mouse leaves element (no bubbling)
- `oncontextmenu` - Right-click on element
- `onwheel` - Mouse wheel is rotated

### Keyboard Events
- `onkeydown` - Key is pressed
- `onkeyup` - Key is released
- `onkeypress` - Key is pressed and released

### Form Events
- `onfocus` - Element receives focus
- `onblur` - Element loses focus
- `onchange` - Element value changes
- `oninput` - Input value changes
- `onsubmit` - Form is submitted
- `onreset` - Form is reset
- `onselect` - Text is selected

### Drag & Drop Events
- `ondrag` - Element is being dragged
- `ondragstart` - Drag operation starts
- `ondragend` - Drag operation ends
- `ondragover` - Element is dragged over a valid drop target
- `ondragenter` - Dragged element enters a valid drop target
- `ondragleave` - Dragged element leaves a valid drop target
- `ondrop` - Element is dropped on a valid drop target

### Scroll & Resize Events
- `onscroll` - Element's scroll position changes
- `onresize` - Element is resized

### Media Events
- `onplay` - Media starts playing
- `onpause` - Media is paused
- `onended` - Media playback completes
- `onvolumechange` - Media volume changes
- `onseeked` - Media seeking completes
- `onseeking` - Media seeking starts
- `ontimeupdate` - Media playback position changes

### Network Events
- `ononline` - Browser goes online
- `onoffline` - Browser goes offline

### Touch Events (Mobile)
- `ontouchstart` - Touch begins on element
- `ontouchmove` - Touch moves on element
- `ontouchend` - Touch ends on element
- `ontouchcancel` - Touch is interrupted

## Event Data

The `EventData` object provides information about the event:

| Property | Type | Description |
|----------|------|-------------|
| `clientX` | int | X coordinate of the mouse pointer |
| `clientY` | int | Y coordinate of the mouse pointer |
| `key` | str | Key pressed (for keyboard events) |
| `deltaX` | int | Horizontal scroll amount |
| `deltaY` | int | Vertical scroll amount |
| `touches` | list | Touch points (for touch events) |
| `timestamp` | int | Time when the event occurred |

## Element Selectors

Elements are typically accessed using selectors in the Template class:

```python
# Get element by ID
button = template.querySelector("#submit-button")

# Get elements by class
items = template.querySelectorAll(".item")

# Get elements by tag name
paragraphs = template.querySelectorAll("p")

# Get element by UUID
specific_element = template.getElementByUUID("12345-67890-abcde")
```
## Example: Form Handling

```python
from pyweber import Template, Element
from pyweber.utils.types import EventType

class ContactForm(Template):
    def __init__(self, app):
        super().__init__(template="contact.html")

        # Get form elements
        self.form = self.querySelector("form")
        self.name_input = self.querySelector("#name")
        self.email_input = self.querySelector("#email")
        self.message_input = self.querySelector("#message")
        self.submit_button = self.querySelector("#submit")
        self.result = self.querySelector("#result")

        # Add event listeners
        self.form.events.onsubmit = self.handle_submit
        self.name_input.events.oninput = self.validate_name
        self.email_input.events.onblur = self.validate_email

    def validate_name(self, e):
        name = self.name_input.value
        if len(name) < 3:
            self.name_input.attrs["class"] = "input-error"
        else:
            self.name_input.attrs["class"] = "input-valid"

    def validate_email(self, e):
        email = self.email_input.value
        if "@" not in email or "." not in email:
            self.email_input.attrs["class"] = "input-error"
        else:
            self.email_input.attrs["class"] = "input-valid"

    def handle_submit(self, e):
        # Prevent default form submission
        # (PyWeber handles this automatically)

        # Get form values
        name = self.name_input.value
        email = self.email_input.value
        message = self.message_input.value

        # Validate
        if len(name) < 3 or "@" not in email:
            self.result.content = "Please fix the errors in the form"
            self.result.add_class("error-message")
            return

        # Process form (in a real app, you'd send this data somewhere)
        self.result.content = f"Thank you, {name}! Your message has been sent."
        self.result.add_class("success-message")

        # Reset form
        self.name_input.value = ""
        self.email_input.value = ""
        self.message_input.value = ""
```
## Best Practices

1. **Use Semantic Elements**: Choose HTML elements that represent their purpose (e.g., `button` for buttons, not `div`).

2. **Maintain Element Hierarchy**: Keep parent-child relationships consistent with the DOM structure.

3. **Event Delegation**: For dynamic content, attach event listeners to parent elements and check the target.

4. **Clean Up Event Listeners**: Remove event listeners when they're no longer needed to prevent memory leaks.

5. **Validate User Input**: Always validate form inputs before processing.

6. **Accessibility**: Set appropriate ARIA attributes for better accessibility.

7. **Performance**: Minimize DOM manipulations by batching changes.

## Advanced Techniques
### Dynamic Element Creation
```python
def add_list_item(self, e):
    # Create a new list item
    new_item = Element(
        tag="li",
        classes=["list-item"],
        content=f"Item {len(self.list.childs) + 1}"
    )

    # Add delete button
    delete_btn = Element(
        tag="button",
        classes=["delete-btn"],
        content="×"
    )
    delete_btn.events.onclick = self.delete_item
    new_item.childs.append(delete_btn)

    # Add to list
    self.list.childs.append(new_item)
```

### Custom Components

You can create reusable components by extending the Element class:
```python
class Card(Element):
    def __init__(self, title, content, image_url=None):
        super().__init__(tag="div", classes=["card"])

        # Create card header
        header = Element(tag="div", classes=["card-header"])
        header.childs.append(Element(tag="h3", content=title))
        self.childs.append(header)

        # Add image if provided
        if image_url:
            img = Element(tag="img", attrs={"src": image_url, "alt": title})
            self.childs.append(img)

        # Add content
        body = Element(tag="div", classes=["card-body"])
        body.childs.append(Element(tag="p", content=content))
        self.childs.append(body)
```
## Next Steps

- Learn about [Templates](template.md) for creating complete pages
- Explore [Router](router.md) for handling navigation
- Understand [Event Handling](events.md) in more detail