# Elements in PyWeber

Elements are the fundamental building blocks of PyWeber applications, representing HTML elements with a powerful object-oriented API for DOM manipulation.

## Creating Elements

Elements can be created programmatically or retrieved from templates:
```python
import pyweber as pw

# Create a button element
button = pw.Element(
    tag="button",
    id="submit-btn",
    classes=["btn", "primary"],
    content="Submit",
    attrs={"type": "submit"}
)

# Create a nested structure
form = pw.Element(
    tag="form",
    id="contact-form",
    childs=[
        pw.Element(tag="input", attrs={"type": "text", "name": "name"}),
        pw.Element(tag="input", attrs={"type": "email", "name": "email"}),
        button
    ]
)
```

## Element Properties

| Property | Type | Description |
|----------|------|-------------|
| `tag` | str | HTML tag name (e.g., "div", "button") |
| `id` | str | Element ID attribute |
| `classes` | list[str] | List of CSS classes |
| `content` | str | Text content of the element |
| `value` | str | Value attribute (for form elements) |
| `style` | dict[str, str] | Dictionary of inline styles |
| `attrs` | dict[str, str] | Dictionary of HTML attributes |
| `childs` | list[Element] | List of child elements |
| `parent` | Element | Parent element |
| `events` | TemplateEvents | Event handlers for this element |
| `uuid` | str | Unique identifier (auto-generated) |
| `data` | Any | Custom data that can be attached to the element |
| `clone` | property | Returns a deep copy of the element with all children |

## Cloning Elements

PyWeber provides a powerful cloning mechanism to create independent copies of elements:

```python
# Create an element with children
original = pw.Element(
    tag="div",
    classes=["container"],
    childs=[
        pw.Element(tag="p", content="Hello world"),
        pw.Element(tag="button", content="Press")
    ]
)

# Create an independent deep copy
copy = original.clone

# Modify the copy without affecting the original
copy.add_class("main")
copy.childs[0].content = "Modified content"
```

The `clone` property performs a deep copy of the entire element tree, ensuring that:
- All properties are copied
- All children are cloned recursively
- UUIDs are preserved for consistent referencing
- Parent-child relationships are maintained

## Advanced Content with Child Elements

PyWeber allows you to combine text content with child elements using a special placeholder syntax:
```python
# Create a button with an icon and text
button = pw.Element(
    tag="button",
    id="action-btn",
    classes=["btn", "primary"]
)

# Create an icon element
icon = pw.Element(
    tag="i",
    classes=["bi", "bi-play-fill"]
)

# Add icon as a child
button.childs = [icon]

# Set content with placeholder for the icon
button.content = f"{{{icon.uuid}}} Start Process"
```

This creates a button with the icon followed by the text "Start Process". The `{uuid}` syntax is a placeholder that will be replaced with the rendered child element.

## Form Components

PyWeber provides pre-built components for common form elements with proper HTML attributes:

```python
# Text input
username = pw.InputText(
    name="username",
    id="user-input",
    placeholder="Enter username",
    required=True,
    autocomplete="username"
)

# Password input with toggleable visibility
password = pw.InputPassword(
    name="password",
    id="password-input",
    placeholder="Enter password",
    showpassword=False,
    autocomplete="current-password"
)

# Text area
comments = pw.TextArea(
    name="comments",
    id="comments-area",
    placeholder="Enter your comments",
    rows=5,
    cols=40
)

# Other input types
email = pw.InputEmail(name="email", required=True)
number = pw.InputNumber(name="quantity", min=1, max=10)
checkbox = pw.InputCheckbox(name="terms", value="accept", checked=False)
date = pw.InputDate(name="birthdate")
file = pw.InputFile(name="upload", accept=".pdf,.jpg")
```

All form components properly handle their specific attributes and events, ensuring correct HTML rendering and behavior.

### Creating Custom Components

You can create reusable components by extending the Element class:
```python
class IconButton(pw.Element):
    def __init__(self, id: str, content: str, icon_classes: list[str], events: pw.TemplateEvents = None):
        super().__init__(tag="button", id=id, events=events)

        # Create icon element
        self.icon = pw.Element(
            tag="i",
            classes=icon_classes
        )

        # Add icon as child
        self.childs = [self.icon]

        # Set content with placeholder
        self.content = f"{{{self.icon.uuid}}} {content}"
```
Usage:
```python
# Create a play button
play_button = IconButton(
    id="play-btn",
    content="Play",
    icon_classes=["bi", "bi-play-fill"],
    events=pw.TemplateEvents(onclick=self.handle_play)
)
```

## Working with Classes
```python
# Add classes
element.add_class("primary")
element.add_class("large bold")  # Add multiple classes

# Remove classes
element.remove_class("secondary")
element.remove_class("small italic")  # Remove multiple classes

# Check if element has a class
if element.has_class("active"):
    print("Element is active")

# Toggle classes (add if not present, remove if present)
element.toggle_class("selected")
element.toggle_class("expanded collapsed")  # Toggle multiple classes
```

## Working with Styles
```python
# Set styles
element.set_style("color", "blue")
element.set_style("font-size", "16px")

# Get styles
color = element.get_style("color")
font_size = element.get_style("font-size", "12px")  # Default if not set

# Remove styles
element.remove_style("background-color")
```

## Working with Attributes
```python
# Set attributes
element.set_attr("data-id", "123")
element.set_attr("aria-label", "Submit form")

# Get attributes
data_id = element.get_attr("data-id")
aria_label = element.get_attr("aria-label", "Button")  # Default if not set

# Remove attributes
element.remove_attr("disabled")
```

## Managing Child Elements
```python
# Add a child element
new_child = pw.Element(tag="span", content="Child text")
parent.add_child(new_child)

# Remove a child element
parent.remove_child(child)

# Remove a child at specific index
parent.pop_child(0)  # Remove first child
parent.pop_child()   # Remove last child

# Access children
first_child = parent.childs[0]
last_child = parent.childs[-1]
```

## Element Selection

Elements provide methods to find child elements:
```python
# Select by CSS selector
button = element.querySelector("#submit-button")
items = element.querySelectorAll(".item")

# Select by attribute
element.getElement(by="id", value="header")
element.getElements(by="classes", value="card")
element.getElements(by="attrs", value="type:submit")
element.getElements(by="style", value="color:blue")
```

## Event Handling

Elements can respond to user interactions through event handlers:

```python
from pyweber.utils.types import EventType

# Method 1: Using events property
button.events.onclick = self.handle_click
input.events.oninput = self.validate_input

# Method 2: Using properties directly on form elements
text_input.onchange = self.handle_change
text_input.onfocus = self.handle_focus
text_input.onblur = self.handle_blur

# Method 3: Using add_event method
button.add_event(EventType.CLICK, self.handle_click)
form.add_event(EventType.SUBMIT, self.handle_submit)

# Remove events
button.remove_event(EventType.CLICK)
```

## Efficient DOM Updates with TemplateDiff

PyWeber uses an intelligent diffing algorithm to efficiently update the DOM:

```python
from pyweber import TemplateDiff

# Create original element structure
original = pw.Element(
    tag="div",
    classes=["container"],
    childs=[
        pw.Element(tag="p", content="Hello world"),
        pw.Element(tag="button", content="Press")
    ]
)

# Create a clone and modify it
modified = original.clone
modified.add_class("main")
modified.childs[0].content = "Updated content"
modified.remove_child(modified.childs[1])
modified.add_child(pw.Element(tag="span", content="New element"))

# Generate diff between versions
diff = TemplateDiff(new_element=modified, old_element=original)

# The diff contains only the actual changes:
# - Added class to container
# - Updated content of paragraph
# - Removed button
# - Added span element
```

This diffing system allows PyWeber to send only the necessary changes to the client, minimizing network traffic and improving performance.

## Example: Clock Component

Here's an example of creating a clock component with nested elements and content placeholders:
```python
import pyweber as pw
from datetime import datetime
import asyncio

class Text(pw.Element):
    def __init__(self, title: str, value: str):
        super().__init__(tag="div")
        self.classes = ['time-element']
        self.childs = [
            pw.Element(tag="p", content=str(value), classes=['time-value']),
            pw.Element(tag="span", content=title)
        ]

class Box(pw.Element):
    def __init__(self, content: str):
        super().__init__(tag="div", classes=["time-box"], content=content)

class Button(pw.Element):
    def __init__(self, value: str, events: pw.TemplateEvents = None):
        super().__init__(
            tag="button", 
            classes=["time-button"],
            value=value,
            events=events
        )

class Title(pw.Element):
    def __init__(self, content: str):
        super().__init__(tag="h2", classes=['time-title'], content=content)

class ClockSpace(pw.Element):
    def __init__(self):
        super().__init__(tag='div', classes=['clock-space'])
        self.childs = [
            Title(content='Clock'),
            pw.Element(
                tag='div',
                classes=['clock-text'],
                childs=[Box(content='00'), Box(content='00'), Box(content='00')]
            ),
            pw.Element(
                tag='div',
                classes=['clock-buttons'],
                childs=[
                    Button(value='start', events=pw.TemplateEvents(onclick=self.start_clock)),
                    Button(value='stop', events=pw.TemplateEvents(onclick=self.stop_clock))
                ]
            )
        ]
    
    async def start_clock(self, e: pw.EventHandler):
        self.is_running = True
        hour, minutes, seconds = e.template.querySelectorAll('.time-box')
        while self.is_running:
            hour.content, minutes.content, seconds.content = await self.get_hour()
            e.update()
            await asyncio.sleep(1)
    
    async def stop_clock(self, e: pw.EventHandler):
        self.is_running = not self.is_running
        hour, minutes, seconds = e.template.querySelectorAll('.time-box')
        hour.content, minutes.content, seconds.content = '00:00:00'.split(':')
        e.update()

    async def get_hour(self) -> tuple[str, str, str]:
        return datetime.now().strftime('%H:%M:%S').split(':')
```

## Best Practices

1. **Use Custom Components**: Create reusable components by extending Element
2. **Use Form Components**: Leverage the built-in form components for proper HTML attributes
3. **Leverage Clone**: Use the clone property when you need independent copies
4. **Combine Content and Children**: Use the `{uuid}` placeholder syntax to mix text and elements
5. **Maintain Element Hierarchy**: Keep parent-child relationships consistent
6. **Update the UI**: Always call `e.update()` after making changes
7. **Use Semantic HTML**: Choose appropriate HTML tags for their intended purpose
8. **Organize Event Handlers**: Keep event handlers focused on specific tasks

## Advanced Techniques

### Dynamic Element Creation
```python
def add_comment(self, e: pw.EventHandler):
    text = self.comment_input.value.strip()
    if text:
        # Create comment with avatar and text
        avatar = pw.Element(
            tag="img",
            classes=["avatar"],
            attrs={"src": "/images/user.png"}
        )

        comment = pw.Element(
            tag="div",
            classes=["comment"]
        )

        # Add avatar as child and use placeholder in content
        comment.childs = [avatar]
        comment.content = f"{{{avatar.uuid}}} {text}"

        # Add to comments section
        self.comments_section.add_child(comment)

        # Clear input
        self.comment_input.value = ""

        e.update()
```

### Using HTMLTag Enum

PyWeber provides an HTMLTag enum for type safety:
```python
from pyweber import HTMLTag

# Create element using enum
header = pw.Element(
    tag=HTMLTag.h1,
    content="Page Title"
)

# Create a list
list_element = pw.Element(tag=HTMLTag.ul)
for i in range(5):
    item = pw.Element(
        tag=HTMLTag.li,
        content=f"Item {i+1}"
    )
    list_element.add_child(item)
```

## Next Steps

- Learn about [Templates](template.md) for creating complete pages
- Explore [Pyweber](router.md) for handling navigation
- Understand [Event Handling](events.md) in more detail