# PyWeber Framework

<img src="https://pyweber.readthedocs.io/en/latest/images/pyweber.png" alt="PyWeber Logo">

[![PyPI version](https://img.shields.io/pypi/v/pyweber.svg)](https://pypi.org/project/pyweber/) [![Coverage Status](https://coveralls.io/repos/github/pyweber/pyweber/badge.svg?branch=master)](https://coveralls.io/github/pyweber/pyweber?branch=master) [![License](https://img.shields.io/pypi/l/pyweber.svg)](https://github.com/pyweber/pyweber/blob/master/LICENSE)

PyWeber is a lightweight Python web framework designed to create dynamic, reactive web applications with a simple and intuitive API. It combines the simplicity of Python with the reactivity of modern frontend frameworks.

## Key Features

- **Reactive Templates**: Create dynamic UIs that automatically update when data changes
- **Component-Based Architecture**: Build reusable components for consistent interfaces
- **Integrated Hot Reload**: See changes instantly during development
- **Intuitive DOM Manipulation**: Query and modify elements with familiar selectors
- **Event-Driven Programming**: Handle user interactions with Python event handlers
- **WebSocket Integration**: Real-time communication between client and server
- **Minimal Configuration**: Get started quickly with sensible defaults

## Quick Start

### Installation

```bash
pip install pyweber
```

### Create a Project

```bash
# Create a new project with configuration
pyweber create-new my_app --with-config
cd my_app
```

### Build a Simple Counter
```python
import pyweber as pw

class Counter(pw.Template):
    def __init__(self, app: pw.Pyweber):
        super().__init__(template="""
            <div>
                <h1>PyWeber Counter</h1>
                <p>Count: <span id="count">0</span></p>
                <button id="increment">Increment</button>
            </div>
        """)

        self.count = self.querySelector("#count")
        self.button = self.querySelector("#increment")
        self.button.events.onclick = self.increment

    async def increment(self, e: pw.EventHandler):
        current = int(self.count.content)
        self.count.content = str(current + 1)
        e.update()

def main(app: pw.Pyweber):
    app.add_route("/", template=Counter(app=app))

if __name__ == "__main__":
    pw.run(target=main)
```

Run your application:

```bash
pyweber run --reload
```

## Core Components

### Pyweber

The main application class that handles routing, middleware, and template management:
```python
app = pw.Pyweber()
app.add_route("/", template=HomePage(app=app))
app.add_route("/users/{user_id}", template=UserProfile(app=app))
```

### Template

Templates represent pages or components with HTML structure and Python logic:
```python
class HomePage(pw.Template):
    def __init__(self, app: pw.Pyweber):
        super().__init__(template="index.html")
        self.title = self.querySelector("h1")
        self.title.content = "Welcome to PyWeber!"
```

### Element

Elements represent DOM nodes that you can manipulate:
```python
# Create elements
button = pw.Element(tag="button", content="Click me", id="my-button")

# Modify properties
button.content = "Clicked!"
button.attributes["disabled"] = "true"
button.style["color"] = "red"
button.add_class("active")
```

### Events

Handle user interactions with Python functions:
```python
# Define event handlers
async def handle_click(e: pw.EventHandler):
    e.element.content = "Processing..."
    await process_data()
    e.element.content = "Done!"
    e.update()

# Attach events
button.events.onclick = handle_click
```

### Window

Interact with the browser window:
```python
# Access window properties
width = template.window.inner_width
scroll_pos = template.window.scroll_y

# Register window events
template.window.events.onresize = handle_resize
template.window.events.onscroll = handle_scroll
```

## Comparison with Other Frameworks

| Feature | PyWeber | Flask | Django | React |
|---------|---------|-------|--------|-------|
| Learning Curve | Low | Low | High | High |
| Reactivity | Built-in | Manual | Manual | Built-in |
| DOM Manipulation | Python API | JavaScript | JavaScript | JSX |
| Hot Reload | Built-in | Add-on | Add-on | Built-in |
| Template Language | Python + HTML | Jinja2 | DTL | JSX |
| Server-Side | Yes | Yes | Yes | No (by default) |
| Configuration | Simple TOML | Environment vars | settings.py | package.json |
| CLI Tools | Comprehensive | Limited | Extensive | Extensive |

## Configuration

PyWeber provides a flexible configuration system:
```python
# Access configuration
from pyweber.config.config import config

# Get values
port = config.get("server", "port")
debug = config.get("app", "debug")

# Set values
config.set("server", "port", 9000)
```

Create or edit configuration files:

```bash
# Create config file
pyweber create-config-file

# Edit interactively
pyweber --edit
```

## CLI Tools

PyWeber includes a powerful CLI:

```bash
# Create projects
pyweber create-new my_project

# Run applications
pyweber run --reload

# Manage configuration
pyweber add-section --section-name database

# Update framework
pyweber --update
```

Visit [Pyweber Docs](https://pyweber.readthedocs.io/) for complete documentation.