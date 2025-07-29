# Pyweber Class Documentation

The `Pyweber` class is the main application class for the PyWeber web framework. It inherits from multiple manager classes to provide comprehensive web application functionality including routing, middleware, cookies, and error handling.

## Dependencies

```python
import inspect
import json
import os
import re
import webbrowser
from typing import Union, Callable, Any
from dataclasses import dataclass
from pyweber.core.element import Element
from pyweber.core.template import Template
from pyweber.models.request import Request
from pyweber.models.response import Response
from pyweber.utils.types import ContentTypes, StaticFilePath, HTTPStatusCode
from pyweber.utils.loads import LoadStaticFiles
from pyweber.core.window import window
from pyweber.models.middleware import MiddlewareManager
from pyweber.models.error_pages import ErrorPages
from pyweber.models.cookies import CookieManager
from pyweber.models.routes import Route, RedirectRoute, RouteManager
from pyweber.models.openapi import OpenApiProcessor
from pyweber.utils.utils import PrintLine
```

## Pyweber Class

### Class Inheritance
```python
class Pyweber(
    ErrorPages,
    CookieManager,
    MiddlewareManager,
    RouteManager
):
```

The Pyweber class inherits from multiple manager classes, providing:
- **ErrorPages**: Custom error page handling
- **CookieManager**: Cookie management functionality
- **MiddlewareManager**: Request/response middleware processing
- **RouteManager**: Route registration and resolution

### Constructor
```python
def __init__(self, **kwargs):
```

**Parameters:**
- `update_handler`: Optional callback function for file change handling
- `**kwargs`: Additional configuration options

**Initialization:**
- Initializes all parent manager classes
- Adds framework-specific routes (admin, docs, static files)
- Sets up internal state tracking
- Configures request handling

### Properties

#### `request` (Read-only Property)
Returns the current request object being processed.

**Returns:** Current Request instance or None

### Core Methods

#### `async get_response(request: Request) -> Response`
Main method for processing HTTP requests and generating responses.

**Parameters:**
- `request`: Request instance to process

**Returns:** Response instance

**Process Flow:**
1. Validates request type
2. Handles OpenAPI route registration
3. Processes before-request middleware
4. Gets template for the route
5. Converts template to bytes
6. Processes after-request middleware
7. Returns final response

**Raises:**
- `TypeError`: If request is not a Request instance

#### `template_to_bytes(template, content_type, title, process_response) -> ContentResult`
Converts various template types to bytes for HTTP response.

**Parameters:**
- `template`: Template content (Template, Element, dict, list, str, bytes)
- `content_type`: ContentTypes enum value
- `title`: Page title for HTML responses
- `process_response`: Whether to wrap content in full template

**Returns:** ContentResult with processed content

**Supported Template Types:**
- **Template objects**: Processed with title and built to HTML
- **Element objects**: Converted to HTML, optionally wrapped in template
- **Dict/List/Set**: Serialized to JSON
- **Bytes**: Used directly with specified content type
- **Strings**: Encoded to bytes, optionally wrapped in template

#### `async get_template(route: str, method: str = 'GET') -> TemplateResult`
Resolves and processes a route to get the template result.

**Parameters:**
- `route`: URL path to resolve
- `method`: HTTP method (default: 'GET')

**Returns:** TemplateResult with processed template

**Process Flow:**
1. Resolves route path and extracts parameters
2. Checks if route exists and method is allowed
3. Handles redirects if configured
4. Processes route middleware
5. Handles static files if applicable
6. Returns 404 for non-existent routes

#### `get_content_type(route: str) -> ContentTypes`
Determines content type based on file extension in route.

**Parameters:**
- `route`: URL path to analyze

**Returns:** ContentTypes enum value

**Logic:**
- Extracts file extension from route
- Maps extension to ContentTypes
- Returns ContentTypes.unknown for unrecognized extensions
- Defaults to ContentTypes.html for routes without extensions

### Template Processing Methods

#### `_process_template_object(template: Template, title: str, content_type: ContentTypes) -> ContentResult`
Processes Template objects into ContentResult.

#### `_process_element_object(element: Element, title: str, content_type: ContentTypes, process_template: bool) -> ContentResult`
Processes Element objects into ContentResult.

#### `_process_json_object(template: Union[dict, list, set]) -> ContentResult`
Processes JSON-serializable objects into ContentResult.

#### `_process_byte_object(data: bytes, content_type: ContentTypes) -> ContentResult`
Processes byte data into ContentResult.

#### `_process_string_object(data: str, title: str, content_type: ContentTypes, process_response: bool) -> ContentResult`
Processes string data into ContentResult.

### Advanced Processing Methods

#### `async _process_templates(state_result: StateResult) -> TemplateResult`
Processes templates through the complete pipeline including callable resolution and redirects.

**Parameters:**
- `state_result`: Current processing state

**Returns:** Final TemplateResult

**Features:**
- Handles callable templates (functions, lambdas)
- Processes redirect routes
- Manages recursion detection
- Supports async and sync callables
- Prepares callback arguments from request body and route parameters

#### `async _process_redirect_route(state: StateResult, redirect_route: RedirectRoute, redirect_path: str, **kwargs) -> StateResult`
Processes redirect routes with middleware support.

#### `async process_route_middleware(resp: str, middlewares: list[Callable], status_code: int)`
Processes route-specific middleware.

### File Handling Methods

#### `is_file_requested(route: str) -> bool`
Checks if the route requests a file based on file extension pattern.

#### `is_static_file(route: str) -> bool`
Checks if the requested file exists in the filesystem.

#### `normaize_path(route: str) -> str`
Normalizes route path for filesystem access.

#### `load_static_files(path: os.path) -> bytes`
Loads static file content from filesystem.

### Framework Integration Methods

#### `async clone_template(route: str) -> Template`
Creates a clone of a template for a specific route.

#### `update(changed_file: str = None)`
Triggers update handler for file change notifications.

#### `launch_url(url: str, new_page: bool = False)`
Opens URL in web browser.

#### `to_url(url: str, new_page: bool = False, message: str = None) -> Element`
Creates a redirect element with optional message.

#### `run(target: Callable = None, **kwargs)`
Runs the application with specified configuration.

#### `async __call__(scope, receive, send)`
ASGI application interface for deployment.

### Internal Methods

#### `_check_recursion(route: str)`
Prevents infinite recursion in route processing.

#### `__add_framework_routes()`
Adds built-in framework routes (admin, docs, static files).

#### `async __add_openapi_route()`
Dynamically adds OpenAPI documentation route.

#### `__get_routes() -> dict`
Generates OpenAPI schema for all registered routes.

## Usage Examples

### Basic Application Setup
```python
from pyweber import Pyweber
from pyweber.utils.types import ContentTypes

# Create application instance
app = Pyweber()

# Add simple route
app.add_route(
    route="/",
    template="<h1>Welcome to PyWeber!</h1>",
    title="Home Page"
)

# Add API route
app.add_route(
    route="/api/users",
    template=lambda: {"users": [], "total": 0},
    content_type=ContentTypes.json,
    methods=["GET", "POST"]
)

print(app)  # Pyweber(routes=2)
```

### Using Route Decorator
```python
app = Pyweber()

@app.route("/users/{user_id}", methods=["GET"])
def get_user(user_id: int):
    return f"<h1>User {user_id}</h1>"

@app.route("/api/posts", methods=["GET", "POST"], 
           content_type=ContentTypes.json)
async def handle_posts():
    return {"posts": []}
```

### Template Processing
```python
from pyweber.core.template import Template
from pyweber.core.element import Element

app = Pyweber()

# Template object route
@app.route("/template-page")
def template_page():
    return Template(
        template="<h1>{{title}}</h1><p>{{content}}</p>",
        title="Template Page",
        context={"title": "Hello", "content": "World"}
    )

# Element object route
@app.route("/element-page")
def element_page():
    return Element(
        tag="div",
        content=[
            Element(tag="h1", content="Element Page"),
            Element(tag="p", content="Generated with Element")
        ]
    )

# JSON API route
@app.route("/api/data", content_type=ContentTypes.json)
def api_data():
    return {"message": "Hello API", "data": [1, 2, 3]}
```

### Middleware Integration
```python
def auth_middleware(request):
    if not request.headers.get("Authorization"):
        return Response(
            content="<h1>Unauthorized</h1>",
            status_code=401,
            process_response=True
        )
    return None

def logging_middleware(request):
    print(f"Request: {request.method} {request.path}")
    return None

# Add global middleware
app.add_before_request_middleware(auth_middleware)
app.add_before_request_middleware(logging_middleware)

# Add route-specific middleware
@app.route("/protected", middlewares=[auth_middleware])
def protected_route():
    return "<h1>Protected Content</h1>"
```

### Error Handling
```python
app = Pyweber()

# Custom 404 page
app.page_not_found = "<h1>Custom 404 Page</h1><p>Page not found!</p>"

# Route with error handling
@app.route("/may-fail")
def may_fail():
    try:
        # Some operation that might fail
        result = risky_operation()
        return f"<h1>Success: {result}</h1>"
    except Exception as e:
        return f"<h1>Error: {str(e)}</h1>"
```

### Static File Serving
```python
app = Pyweber()

# Static files are automatically served if they exist
# /static/style.css -> serves static/style.css if file exists
# /images/logo.png -> serves images/logo.png if file exists

# Custom static file route
@app.route("/custom-css", content_type=ContentTypes.css)
def custom_css():
    return "body { background-color: #f0f0f0; }"
```

### Redirects
```python
app = Pyweber()

# Add target route
app.add_route("/new-page", template="<h1>New Page</h1>", name="new_page")

# Create redirect
app.redirect("/old-page", "new_page", status_code=301)

# Programmatic redirect in route
@app.route("/login-required")
def login_required():
    if not user_authenticated():
        return app.to_route("login_page")
    return "<h1>Welcome!</h1>"
```

### Request Processing
```python
app = Pyweber()

@app.route("/form-handler", methods=["POST"])
def handle_form(name: str, email: str, age: int = 18):
    # Parameters automatically extracted from request body
    return f"<h1>Hello {name}!</h1><p>Email: {email}, Age: {age}</p>"

@app.route("/user-info")
def user_info():
    # Access current request
    request = app.request
    user_agent = request.headers.get("User-Agent", "Unknown")
    return f"<h1>Your User Agent: {user_agent}</h1>"
```

### Running the Application
```python
app = Pyweber()

# Add routes...
app.add_route("/", template="<h1>Hello World</h1>")

# Run development server
app.run(host="127.0.0.1", port=8000, debug=True)

# Or run with custom target function
def custom_server():
    print("Starting custom server...")
    # Custom server logic

app.run(target=custom_server, host="0.0.0.0", port=5000)
```

### ASGI Deployment
```python
# app.py
from pyweber import Pyweber

app = Pyweber()

@app.route("/")
def home():
    return "<h1>Production App</h1>"

# Deploy with ASGI server (uvicorn, gunicorn, etc.)
# uvicorn app:app --host 0.0.0.0 --port 8000
```

## Advanced Features

### OpenAPI Documentation
```python
app = Pyweber()

@app.route("/api/users/{user_id}", methods=["GET"])
def get_user(user_id: int):
    """Get user by ID"""
    return {"user_id": user_id, "name": "John Doe"}

# OpenAPI spec automatically available at:
# /_pyweber/{uuid}/openapi.json
# Documentation UI available at: /docs
```

### Template Cloning
```python
app = Pyweber()

@app.route("/template")
def template_route():
    return Template(template="<h1>{{title}}</h1>", title="Original")

# Clone template for modification
async def clone_example():
    cloned = await app.clone_template("/template")
    cloned.context["title"] = "Cloned"
    return cloned.build_html()
```

### File Change Handling
```python
def handle_file_change(module):
    print(f"File changed: {module}")
    # Reload logic here

app = Pyweber(update_handler=handle_file_change)

# Trigger update
app.update("my_module.py")
```

### Browser Integration
```python
app = Pyweber()

@app.route("/open-external")
def open_external():
    app.launch_url("https://example.com", new_page=True)
    return "<h1>External page opened</h1>"

@app.route("/redirect-with-message")
def redirect_with_message():
    return app.to_url(
        url="/target-page",
        new_page=False,
        message="Redirecting to target page..."
    )
```

## Framework Routes

PyWeber automatically adds several built-in routes:

### Admin Routes
- `/admin` - Admin panel interface
- `/_pyweber/admin/{uuid}/.css` - Admin CSS files
- `/_pyweber/admin/{uuid}/.js` - Admin JavaScript files

### Documentation Routes
- `/docs` - PyWeber documentation
- `/_pyweber/{uuid}/openapi.json` - OpenAPI specification

### Static Asset Routes
- `/_pyweber/static/favicon.ico` - Framework favicon
- `/_pyweber/static/{uuid}/.css` - Framework CSS files
- `/_pyweber/static/{uuid}/.js` - Framework JavaScript files

## Error Handling

### Built-in Error Pages
```python
app = Pyweber()

# Customize error pages
app.page_not_found = "<h1>Custom 404</h1>"
app.internal_server_error = "<h1>Custom 500</h1>"
```

### Middleware Error Handling
```python
def error_handling_middleware(request):
    try:
        # Process request
        return None
    except Exception as e:
        return Response(
            content=f"<h1>Middleware Error: {str(e)}</h1>",
            status_code=500,
            process_response=True
        )

app.add_before_request_middleware(error_handling_middleware)
```

## Performance Considerations

### Template Processing
- Templates are processed on each request
- Use caching for expensive template operations
- Consider static file serving for unchanging content

### Route Resolution
- Route resolution uses pattern matching
- Large numbers of routes may impact performance
- Use route groups for organization

### Middleware Chain
- Middleware is processed in order for each request
- Keep middleware lightweight
- Use early returns to avoid unnecessary processing

### Static File Serving
- Static files are served directly from filesystem
- Consider using a reverse proxy for production static file serving
- File existence is checked on each request

## Best Practices

### Application Structure
```python
# Organize routes logically
app = Pyweber()

# API routes
@app.route("/api/users", methods=["GET", "POST"], group="api")
def users_api():
    return {"users": []}

# Web pages
@app.route("/", name="home")
def home():
    return Element('h1', content='Home Page')

# Admin routes
@app.route("/admin/dashboard", middlewares=[admin_auth])
def admin_dashboard():
    return Element('h1', content='Dashboard Page')
```

### Error Handling
```python
# Centralized error handling
def global_error_handler(request):
    try:
        return None  # Continue processing
    except Exception as e:
        logger.error(f"Request error: {e}")
        return Response(
            content="<h1>Something went wrong</h1>",
            status_code=500,
            process_response=True
        )

app.add_before_request_middleware(global_error_handler)
```

### Security
```python
# Security middleware
def security_middleware(response):
    response.headers.update({
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block"
    })
    return response

app.add_after_request_middleware(security_middleware)
```

### Development vs Production
```python
import os

app = Pyweber()

# Environment-specific configuration
if os.getenv("ENVIRONMENT") == "development":
    app.run(debug=True, reload=True)
else:
    # Production deployment with ASGI server
    # uvicorn app:app --host 0.0.0.0 --port 8000 --workers 4
    pass
```

## Thread Safety

- Pyweber instances are not inherently thread-safe
- Each request should be processed independently
- Avoid shared mutable state between requests
- Use proper synchronization for shared resources

## Integration Examples

### Database Integration
```python
import sqlite3
from pyweber import Element

app = Pyweber()

def get_db():
    return sqlite3.connect("app.db")

@app.route("/users/{user_id}")
def get_user(user_id: int):
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    db.close()

    if user:
        return Element('h1', content=f'User: {user[1]}')
    else:
        return app.page_not_found
```

### Template Engine Integration
```python
from jinja2 import Environment, FileSystemLoader

app = Pyweber()
jinja_env = Environment(loader=FileSystemLoader("templates"))

@app.route("/jinja-template")
def jinja_template():
    template = jinja_env.get_template("page.html")
    return template.render(title="Jinja Page", content="Hello from Jinja!")
```

### API Integration
```python
import requests

app = Pyweber()

@app.route("/api/external-data", content_type=ContentTypes.json)
async def external_data():
    response = requests.get("https://api.example.com/data")
    return response.json()
```