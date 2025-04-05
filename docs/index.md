# PyWeber Framework

![PyWeber Logo](images/pyweber.png)

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

## Installation

Install PyWeber using pip:

```bash
pip install pyweber
```

## Quick Start

### Create a New Project

The easiest way to get started is to use the PyWeber CLI:

```bash
pyweber create-new my_first_app
cd my_first_app
```

### Or Start from Scratch

Create a simple counter application:

```python
import pyweber as pw

class Counter(pw.Template):
    def __init__(self, app: pw.Router):
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

    def increment(self, e: pw.EventHandler):
        current = int(self.count.content)
        self.count.content = str(current + 1)
        e.update()

def main(app: pw.Router):
    app.add_route("/", template=Counter(app=app))

if __name__ == "__main__":
    pw.run(target=main)
```

Run your application:

```bash
python main.py
# or use the CLI
pyweber run
```

Visit `http://localhost:8800` in your browser to see your application.

## Core Concepts

### Templates

Templates in PyWeber represent complete pages or reusable components. They combine HTML structure with Python logic:

```python
class MyTemplate(pw.Template):
    def __init__(self, app: pw.Router):
        super().__init__(template="path/to/template.html")
        # or inline HTML
        # super().__init__(template="<h1>Hello World</h1>")
```

### Elements

Elements represent DOM nodes that you can manipulate:

```python
# Select elements
title = template.querySelector("h1")
buttons = template.querySelectorAll(".button")

# Modify content
title.content = "New Title"

# Change attributes
image.attributes["src"] = "/path/to/image.jpg"

# Modify styles
button.style["background-color"] = "blue"

# Work with classes
button.classes.add("active")
button.classes.remove("disabled")
```

### Events

Handle user interactions with Python functions:

```python
def button_click(e: pw.EventHandler):
    e.element.content = "Clicked!"

button.events.onclick = button_click
```

### Routing

Define routes to different templates:

```python
def main(app: pw.Router):
    app.add_route("/", template=HomePage(app=app))
    app.add_route("/about", template=AboutPage(app=app))
    app.add_route("/users/{user_id}", template=UserProfile(app=app))
```

## Why PyWeber?

PyWeber bridges the gap between backend and frontend development by allowing Python developers to create dynamic web interfaces without extensive JavaScript knowledge. It's ideal for:

- **Prototyping**: Quickly build interactive prototypes
- **Internal Abilities**: Create admin panels and dashboards
- **Small to Medium Applications**: Build complete web applications with a single language
- **Learning Web Development**: Understand web concepts with familiar Python syntax

## Comparison with Other Frameworks

| Feature | PyWeber | Flask | Django | React |
|---------|---------|-------|--------|-------|
| Learning Curve | Low | Low | High | High |
| Reactivity | Built-in | Manual | Manual | Built-in |
| DOM Manipulation | Python API | JavaScript | JavaScript | JSX |
| Hot Reload | Built-in | Add-on | Add-on | Built-in |
| Template Language | Python + HTML | Jinja2 | DTL | JSX |
| Server-Side | Yes | Yes | Yes | No (by default) |

## Next Steps

- [Installation Guide](installation.md)
- [CLI Documentation](cli.md)
- [Template System](template.md)
- [Router Documentation](router.md)
- [Examples](https://github.com/pyweber/pyweber-examples.git)

## Community and Support

- [GitHub Repository](https://github.com/pyweber/pyweber)
- [Documentation](https://pyweber.readthedocs.io/)
- [Issue Tracker](https://github.com/pyweber/pyweber/issues)

## License

PyWeber is released under the MIT License. See the LICENSE file for details.