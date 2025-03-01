# PyWeber - A Lightweight Python Framework

<img src="https://pyweber.readthedocs.io/en/latest/images/pyweber.png" alt="PyWeber Logo">

[![PyPI version](https://img.shields.io/pypi/v/pyweber.svg)](https://pypi.org/project/pyweber/) [![Coverage Status](https://coveralls.io/repos/github/pyweber/pyweber/badge.svg?branch=master)](https://coveralls.io/github/pyweber/pyweber?branch=master) [![License](https://img.shields.io/pypi/l/pyweber.svg)](https://github.com/pyweber/pyweber/blob/master/LICENSE)

PyWeber is a Python library for creating and managing HTML templates dynamically, as well as providing a simple routing system for web applications. With PyWeber, you can create, manipulate, and render HTML elements programmatically, in addition to managing routes and redirects.

## Installation

To install PyWeber, use pip:

```bash
pip install pyweber
```

## Basic Usage
### Creating a New Project
To create a new project with PyWeber, use the CLI command:
```bash
pyweber create-new my_project
```

This will create a basic directory structure for your project, including the files `main.py`, `index.html`, and `style.css`.

### Running the Project
To run the project, use the command:
```bash
cd my_project
pyweber run
```

This will start the server and execute the project defined in the `main.py` file.

### Updating PyWeber
To update the PyWeber library to the latest version, use the command:

```bash
pyweber update
```

## Usage Example
Here is a basic example of how to use PyWeber to create a dynamic HTML page:

```python
import pyweber as pw
from pyweber import Element

class Home(pw.Template):
    def __init__(self):
        super().__init__(template='index.html')

def main(app: pw.Router):
    app.add_route(route='/', template=Home())

if __name__ == '__main__':
    pw.run(target=main, reload=True)
```

## Main Classes and Methods
### Element
The Element class represents an HTML element. It has the following attributes:

- `name`: Name of the HTML tag (e.g., div, p, etc.).
- `id`: Element ID.
- `class_name`: CSS class of the element.
- `content`: Text content of the element.
- `attributes`: Dictionary of HTML attributes.
- `parent`: Parent element.
- `childs`: List of child elements.

### Template
The Template class is responsible for loading and manipulating HTML templates. It has methods for:
- `read_file`: Reads the content of an HTML file.
- `parse`: Parses the HTML and returns the element structure.
- `rebuild_html`: Rebuilds the HTML from the element structure.
- `getElementById`, `getElementByClass`, `querySelector`, `querySelectorAll`: Methods for finding elements in the template.

### Router
The Router class manages the application's routes. It allows:
- Adding, updating, and removing routes.
- Redirecting one route to another.
- Checking if a route exists or if it is a redirect.

### run
The `run` function starts the server and runs the application. It accepts the following parameters:
- `target`: Function that defines the routes.
- `route`: Initial route (default: `/`).
- `reload`: Whether to automatically reload on changes (default: `True`).
- `port`: Server port (default: `8800`).

## Contribution
Contributions are welcome! Feel free to open issues and pull requests in the PyWeber repository.

## License
PyWeber is licensed under the MIT License.

## Contacts
- Author: DevPythonMZ
- Email: zoidycine@gmail.com
- GitHub: https://github.com/webtechmoz/pyweber