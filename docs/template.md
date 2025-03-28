# Templates in PyWeber

Templates are the core building blocks of PyWeber applications. They represent HTML pages or components that can be dynamically manipulated through Python code.

## Creating Templates

A template in PyWeber can be created from an HTML file or from an HTML string:

```python
import pyweber as pw

# From an HTML file
class PageTemplate(pw.Template):
    def __init__(self, app: pw.Router):
        super().__init__(template="page.html")

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

# From an HTML string
class InlineTemplate(pw.Template):
    def __init__(self, app: pw.Router):
        super().__init__(template="""
            <div>
                <h1>Inline Template</h1>
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

### Element Selection Methods

PyWeber provides several methods to select elements within a template:

#### querySelector

```python
querySelector(selector: str, element: Element = None) -> Element | None
```

Selects the first element that matches the CSS selector.

```python
# Select by ID
button = template.querySelector("#submit-button")

# Select by class
title = template.querySelector(".main-title")

# Select by tag name
paragraph = template.querySelector("p")
```
#### querySelectorAll

```python
querySelectorAll(selector: str, element: Element = None) -> list[Element]
```
Selects all elements that match the CSS selector.

```python
# Select all paragraphs
paragraphs = template.querySelectorAll("p")

# Select all elements with a specific class
items = template.querySelectorAll(".item")
```
#### getElementById

```python
getElementById(element_id: str, element: Element = None) -> Element | None
```

Selects an element by its ID.
```python
button = template.getElementById("submit-button")
```

#### getElementByClass

```python
getElementByClass(class_name: str, element: Element = None) -> list[Element]
```
Selects all elements with the specified class.

```python
items = template.getElementByClass("item")
```

### HTML Manipulation

#### parse_html
```python
parse_html(html: str = None) -> Element
```

Parses HTML into an Element tree. If no HTML is provided, uses the template's HTML.

```python
# Parse new HTML and replace the current template
new_element = template.parse_html("<div><h1>New Content</h1></div>")
template.root = new_element
```

#### build_html
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
image.attrs["src"] = "/images/new-image.jpg"
image.attrs["alt"] = "New Image"

# Change styles (inline)
button = template.querySelector("button")
button.style = {"background-color": "blue"; "color": "white"}

# Work with classes
button.classes = ["primary-button"]  # Replace all classes
# or
button_element = template.querySelector(".btn")
current_classes = button_element.classes
if "active" not in current_classes:
    button_element.add_class("active")
```

## Handling Events

Events in PyWeber are handled by Python functions:

```python
class MyTemplate(pw.Template):
    def __init__(self, app: pw.Router):
        super().__init__(template="template.html")

        self.button = self.querySelector("#my-button")
        self.input = self.querySelector("#my-input")

        # Assign event handlers
        self.button.events.onclick = self.handle_click
        self.input.events.oninput = self.handle_input

    def handle_click(self, e: pw.EventHandler):
        """Handle button click event"""
        self.button.content = "Clicked!"

    def handle_input(self, e: pw.EventHandler):
        """Handle input change event"""
        value = e.data.get("value", "")
        self.button.content = f"Input: {value}"
```
### Available Events

PyWeber supports a wide range of DOM events, including:

- **Mouse Events**: `onclick`, `ondblclick`, `onmousedown`, `onmouseup`, etc.
- **Keyboard Events**: `onkeydown`, `onkeyup`, `onkeypress`
- **Form Events**: `onfocus`, `onblur`, `onchange`, `oninput`, `onsubmit`
- **Drag & Drop Events**: `ondrag`, `ondragstart`, `ondragend`, `ondrop`, etc.
- **Media Events**: `onplay`, `onpause`, `onended`, etc.
- **Touch Events**: `ontouchstart`, `ontouchend`, `ontouchmove`

## Template Lifecycle

1. **Initialization**: The template is created and HTML is parsed
2. **Element Selection**: Elements are selected and stored as properties
3. **Event Binding**: Event handlers are attached to elements
4. **Rendering**: The template is rendered when its route is accessed
5. **Event Handling**: Events trigger Python functions that update elements
6. **Updates**: Changes to elements are sent to the client via WebSocket

## Advanced Features

### Custom Status Codes

You can set custom HTTP status codes for templates:

```python
class NotFoundTemplate(pw.Template):
    def __init__(self, app: pw.Router):
        super().__init__(template="404.html", status_code=404)
```

### Dynamic Element Creation

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

    # Add to container
    container.childs.append(new_item)
```

### Template Composition

You can compose templates by nesting them:
```python
class HeaderTemplate(pw.Template):
    def __init__(self):
        super().__init__(template="header.html")
        self.logo = self.querySelector(".logo")

class PageTemplate(pw.Template):
    def __init__(self, app: pw.Router):
        super().__init__(template="page.html")

        # Create header
        self.header = HeaderTemplate()

        # Get the header container
        header_container = self.querySelector("#header-container")

        # Replace with our header template's root
        header_container.childs = [self.header.root]
```

## Best Practices

1. **Organize Templates**: Create separate template classes for different pages or components
2. **Meaningful Names**: Use descriptive names for element variables
3. **Separation of Concerns**: Keep event handlers focused on specific tasks
4. **Reuse Components**: Create reusable template components for common UI elements
5. **Validate Input**: Always validate user input before processing

## Example: Complete Form Template
```python
class ContactForm(pw.Template):
    def __init__(self, app: pw.Router):
        super().__init__(template="contact_form.html")

        # Select form elements
        self.form = self.querySelector("form")
        self.name_input = self.querySelector("#name")
        self.email_input = self.querySelector("#email")
        self.message_input = self.querySelector("#message")
        self.submit_button = self.querySelector("#submit")
        self.error_message = self.querySelector(".error-message")
        self.success_message = self.querySelector(".success-message")

        # Hide messages initially
        self.error_message.attrs["style"] = "display: none;"
        self.success_message.attrs["style"] = "display: none;"

        # Bind events
        self.form.events.onsubmit = self.handle_submit

    def handle_submit(self, e: pw.EventHandler):
        # Get form data
        name = self.name_input.value
        email = self.email_input.value
        message = self.message_input.value

        # Validate
        if not name or not email or not message:
            self.show_error("All fields are required")
            return

        if "@" not in email:
            self.show_error("Invalid email address")
            return

        # Process form (in a real app, you'd send this data somewhere)
        self.show_success("Thank you for your message!")

        # Reset form
        self.name_input.value = ""
        self.email_input.value = ""
        self.message_input.value = ""

    def show_error(self, message: str):
        self.error_message.content = message
        self.error_message.attrs["style"] = "display: block;"
        self.success_message.attrs["style"] = "display: none;"

    def show_success(self, message: str):
        self.success_message.content = message
        self.success_message.attrs["style"] = "display: block;"
        self.error_message.attrs["style"] = "display: none;"
```
## Next Steps

- Learn about [Elements](elements.md) in detail
- Explore [Routing](router.md) to connect templates to URLs
- Understand [Event Handling](events.md) for interactive applications