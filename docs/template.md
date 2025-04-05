# Templates in PyWeber

Templates are the core building blocks of PyWeber applications. They represent HTML pages or components that can be dynamically manipulated through Python code.

## Creating Templates

A template in PyWeber can be created from an HTML file or from an HTML string:

```python
import pyweber as pw

# From an HTML file in the templates directory
class HomePage(pw.Template):
    def __init__(self, app: pw.Pyweber):
        super().__init__(template="home.html")

        # Initialize elements and events
        self.setup()

    def setup(self):
        # Select and manipulate elements
        self.title = self.querySelector("h1")
        self.button = self.querySelector("#action-button")

        # Add event handlers
        self.button.events.onclick = self.handle_click

    def handle_click(self, e: pw.EventHandler):
        self.title.content = "Button was clicked!"
        e.update()  # Update the UI

# From an HTML string
class SimpleTemplate(pw.Template):
    def __init__(self, app: pw.Pyweber):
        super().__init__(template="""
            <div>
                <h1>Simple Template</h1>
                <button id="action-button">Click Me</button>
            </div>
        """)

        # Initialize as before
        self.setup()
```

## Template Class API

### Constructor

Template(template: str, status_code: int = 200)

- `template`: Path to an HTML file (relative to the templates directory) or an HTML string
- `status_code`: HTTP status code to return when this template is rendered (default: 200)

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `template` | str | The raw HTML template string |
| `root` | Element | The root element of the parsed HTML |
| `status_code` | int | The HTTP status code for this template |
| `events` | dict | Dictionary of registered event handlers |
| `data` | Any | Custom data that can be attached to the template |

## Element Selection Methods

PyWeber provides several methods to select elements within a template:

### querySelector

```python
querySelector(selector: str, element: Element = None) -> Element | None

Selects the first element that matches the CSS selector.

# Select by ID
button = template.querySelector("#submit-button")

# Select by class
title = template.querySelector(".main-title")

# Select by tag name
paragraph = template.querySelector("p")

### querySelectorAll

querySelectorAll(selector: str, element: Element = None) -> list[Element]

Selects all elements that match the CSS selector.

# Select all paragraphs
paragraphs = template.querySelectorAll("p")

# Select all elements with a specific class
items = template.querySelectorAll(".item")
```

### getElementById
```python
getElementById(element_id: str, element: Element = None) -> Element | None
```

Selects an element by its ID.
```python
button = template.getElementById("submit-button")
```

### getElementByClass
```python
getElementByClass(class_name: str, element: Element = None) -> list[Element]
```

Selects all elements with the specified class.

```python
items = template.getElementByClass("item")
```

### getElementByUUID
```python
getElementByUUID(element_uuid: str, element: Element = None) -> Element | None
```
Selects an element by its UUID (internal identifier).

```python
element = template.getElementByUUID("12345678-1234-5678-1234-567812345678")
```

## HTML Manipulation

### parse_html
```python

parse_html(html: str = None) -> Element
```

Parses HTML into an Element tree. If no HTML is provided, uses the template's HTML.

```python
# Parse new HTML and replace the current template
new_element = template.parse_html("<div><h1>New Content</h1></div>")
template.root = new_element
```

### build_html
```python
build_html(element: Element = None) -> str
```
Builds HTML string from the Element tree. If no element is provided, uses the template's root element.
```python
# Get the current HTML
html = template.build_html()

# Get HTML for a specific element
div_html = template.build_html(template.querySelector("div"))
```

## Working with Elements

Elements in a template can be manipulated after selection:
```python
# Change content
title = template.querySelector("h1")
title.content = "New Title"

# Change attributes
image = template.querySelector("img")
image.set_attr("src", "/images/new-image.jpg")
image.set_attr("alt", "New Image")

# Change styles
button = template.querySelector("button")
button.set_style("background-color", "blue")
button.set_style("color", "white")

# Work with classes
button.add_class("primary-button")
button.remove_class("disabled")
button.toggle_class("active")  # Add if not present, remove if present
```
## Element Properties and Methods

Elements have various properties and methods for manipulation:

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `tag` | str | The HTML tag name |
| `id` | str | The element's ID attribute |
| `content` | str | The text content of the element |
| `value` | str | The value attribute (for form elements) |
| `classes` | list[str] | List of CSS classes |
| `style` | dict[str, str] | Dictionary of inline styles |
| `attrs` | dict[str, str] | Dictionary of HTML attributes |
| `childs` | list[Element] | List of child elements |
| `events` | TemplateEvents | Event handlers for this element |
| `parent` | Element | The parent element |
| `data` | Any | Custom data that can be attached to the element |

### Methods

#### Class Management
```python
add_class(class_name: str)
remove_class(class_name: str)
has_class(class_name: str) -> bool
toggle_class(class_name: str)
```
#### Style Management
```python
set_style(key: str, value: str)
get_style(key: str, default=None) -> str
remove_style(key: str)
```
#### Attribute Management
```python
set_attr(key: str, value: str)
get_attr(key: str, default=None) -> str
remove_attr(key: str)
```
#### Child Management
```python
add_child(child: Element)
remove_child(child: Element)
pop_child(index: int = -1)
```
#### Element Selection
```python
querySelector(selector: str) -> Element
querySelectorAll(selector: str) -> list[Element]
getElement(by: GetBy, value: str) -> Element
getElements(by: GetBy, value: str) -> list[Element]
```
## Handling Events

Events in PyWeber are handled by Python functions:
```python
class ContactForm(pw.Template):
    def __init__(self, app: pw.Pyweber):
        super().__init__(template="contact_form.html")

        # Select form elements
        self.form = self.querySelector("form")
        self.name_input = self.querySelector("#name")
        self.email_input = self.querySelector("#email")
        self.submit_button = self.querySelector("#submit")
        self.result = self.querySelector("#result")

        # Bind events
        self.submit_button.events.onclick = self.handle_submit
        self.name_input.events.oninput = self.validate_name

    def validate_name(self, e: pw.EventHandler):
        name = self.name_input.value
        if len(name) < 3:
            self.name_input.set_style("border-color", "red")
        else:
            self.name_input.set_style("border-color", "green")
        e.update()

    def handle_submit(self, e: pw.EventHandler):
        name = self.name_input.value
        email = self.email_input.value

        if len(name) < 3 or "@" not in email:
            self.result.content = "Please check your inputs"
            self.result.set_style("color", "red")
        else:
            self.result.content = f"Thank you, {name}! We'll contact you at {email}"
            self.result.set_style("color", "green")

        e.update()
```

### Adding Events

You can add events to elements in several ways:
```python
# Method 1: Using events property
button.events.onclick = self.handle_click

# Method 2: Using add_event method
from pyweber.utils.types import EventType
button.add_event(EventType.CLICK, self.handle_click)

# Method 3: During element creation
button = pw.Element(
    tag="button",
    content="Click Me",
    events=pw.TemplateEvents(
        onclick=self.handle_click
    )
)
```

### Removing Events
```python
# Remove a specific event
button.remove_event(EventType.CLICK)

# Reset all events
button.events = pw.TemplateEvents()
```

## Dynamic Element Creation

You can create and modify elements dynamically:
```python
def add_item(self, e: pw.EventHandler):
    # Get the container
    container = self.querySelector("#items-container")

    # Create a new item
    new_item = pw.Element(
        tag="div",
        classes=["item"],
        content=f"Item {len(container.childs) + 1}"
    )

    # Create a delete button
    delete_btn = pw.Element(
        tag="button",
        classes=["delete-btn"],
        content="×"
    )

    # Add event to the delete button
    delete_btn.events.onclick = self.delete_item

    # Add button to item
    new_item.add_child(delete_btn)

    # Add to container
    container.childs.append(new_item)

    e.update()

def delete_item(self, e: pw.EventHandler):
    # Get the button that was clicked
    button = e.element

    # Get the parent item
    item = button.parent

    # Get the container
    container = item.parent

    # Remove the item from the container
    container.remove_child(item)

    e.update()
```
## Example: Todo List Application

Here's a complete example of a simple todo list application:
```python
import pyweber as pw

class TodoList(pw.Template):
    def __init__(self, app: pw.Pyweber):
        super().__init__(template="""
            <div class="container">
                <h1>Todo List</h1>
                <div class="input-group">
                    <input id="new-todo" type="text" placeholder="Add new item">
                    <button id="add-button">Add</button>
                </div>
                <ul id="todo-list"></ul>
            </div>
        """)

        self.input = self.querySelector("#new-todo")
        self.add_button = self.querySelector("#add-button")
        self.todo_list = self.querySelector("#todo-list")

        # Initialize empty list
        self.todos = []

        # Add event handlers
        self.add_button.events.onclick = self.add_todo
        self.input.events.onkeydown = self.handle_key

    def handle_key(self, e: pw.EventHandler):
        if e.event_data.key == "Enter":
            self.add_todo(e)

    def add_todo(self, e: pw.EventHandler):
        text = self.input.value
        if text:
            # Create new list item
            item = pw.Element(
                tag="li",
                classes=["todo-item"]
            )

            # Create text span
            text_span = pw.Element(
                tag="span",
                content=text,
                classes=["todo-text"]
            )

            # Create delete button
            delete_btn = pw.Element(
                tag="button",
                content="×",
                classes=["delete-btn"]
            )
            delete_btn.events.onclick = self.delete_todo

            # Add elements to item
            item.add_child(text_span)
            item.add_child(delete_btn)

            # Add to list
            self.todo_list.childs.append(item)
            self.todos.append(text)

            # Clear input
            self.input.value = ""

            e.update()

    def delete_todo(self, e: pw.EventHandler):
        # Get the button that was clicked
        button = e.element

        # Get the parent item
        item = button.parent

        # Find the text span
        text_span = item.querySelector(".todo-text")

        # Remove from our data
        if text_span.content in self.todos:
            self.todos.remove(text_span.content)

        # Remove from DOM
        self.todo_list.remove_child(item)

        e.update()

def main(app: pw.Pyweber):
    app.add_route("/", template=TodoList(app=app))

if __name__ == "__main__":
    pw.run(target=main)
```

## Best Practices

1. **Organize Templates**: Create separate template classes for different pages or components
2. **Meaningful Names**: Use descriptive names for element variables
3. **Separation of Concerns**: Keep event handlers focused on specific tasks
4. **Update the UI**: Always call `e.update()` after making changes to ensure the UI is refreshed
5. **Reuse Components**: Create reusable template components for common UI elements
6. **Validate Input**: Always validate user input before processing

## Next Steps

- Learn about [Elements](element.md) in detail
- Explore [Routing](router.md) to connect templates to URLs
- Understand [Event Handling](events.md) for interactive applications