# Route Class Documentation

The `Route` class represents an individual route definition in the PyWeber framework. It encapsulates all the configuration needed to handle HTTP requests for a specific URL pattern, including templates, methods, middleware, and response settings.

## Dependencies

```python
import inspect
import re
from string import punctuation
from typing import Union, Callable, Any
from pyweber.core.element import Element
from pyweber.core.template import Template
from pyweber.utils.types import ContentTypes, HTTPStatusCode
from pyweber.models.routes import RedirectRoute
from pyweber.exceptions import InvalidRouteFormatError
```

## Route Class

### Constructor
```python
def __init__(
    self,
    route: str,
    template: Union[RedirectRoute, Template, Element, Callable, dict, str],
    group: str = None,
    methods: list[str] = None,
    name: str = None,
    middlewares: list[Callable] = None,
    status_code: int = None,
    content_type: ContentTypes = None,
    title: str = '',
    process_response: bool = True,
    callback: Callable[..., Any] = None,
    **kwargs
):
```

**Parameters:**
- `route`: URL pattern for the route (must start with '/')
- `template`: Content to serve (Template, Element, Callable, dict, str, or RedirectRoute)
- `group`: Optional group name for organizing routes
- `methods`: List of allowed HTTP methods (default: ['GET'])
- `name`: Optional name for the route (used for URL generation)
- `middlewares`: List of middleware functions to apply
- `status_code`: HTTP status code to return (default: 200)
- `content_type`: Response content type (default: ContentTypes.html)
- `title`: Page title for HTML responses
- `process_response`: Whether to wrap response in full template
- `callback`: Function to call when route is accessed
- `**kwargs`: Additional route parameters

### Properties

#### `callback` (Property with Setter)
Gets or sets the callback function for the route.

**Getter Returns:** Callable function that processes the route

**Setter Parameters:**
- `callback`: Callable function or None

**Behavior:**
- If callback is provided, validates it's callable
- If no callback provided, uses template as callback if it's callable
- Otherwise creates lambda that returns the template

#### `full_route` (Read-only Property)
Returns the complete route path including group prefix.

**Returns:** Full route string with group prefix

**Logic:**
- If group is not default group, prepends `/{group}{route}`
- Otherwise returns route as-is

#### `middlewares` (Property with Setter)
Gets or sets the middleware functions for the route.

**Getter Returns:** List of middleware functions

**Setter Parameters:**
- `middlewares`: List of callable functions

**Validation:**
- Must be a list
- All items must be callable functions

**Raises:**
- `TypeError`: If middlewares is not a list
- `ValueError`: If any middleware is not callable

#### `methods` (Property with Setter)
Gets or sets the allowed HTTP methods for the route.

**Getter Returns:** List of uppercase HTTP method strings

**Setter Parameters:**
- `methods`: List of HTTP method strings

**Validation:**
- Must be a list
- All methods must be in allowed methods list
- Automatically converts to uppercase

**Raises:**
- `TypeError`: If methods is not a list
- `ValueError`: If any method is not allowed

#### `status_code` (Property with Setter)
Gets or sets the HTTP status code for the route.

**Getter Returns:** HTTP status code integer

**Setter Parameters:**
- `value`: HTTP status code integer

**Validation:**
- Defaults to 200 if None provided
- Must be a valid HTTP status code

**Raises:**
- `ValueError`: If status code is not valid

#### `content_type` (Property with Setter)
Gets or sets the response content type.

**Getter Returns:** ContentTypes enum value

**Setter Parameters:**
- `value`: ContentTypes enum value

**Validation:**
- Cannot be None or empty
- Must be ContentTypes instance

**Raises:**
- `ValueError`: If content_type is empty
- `TypeError`: If not ContentTypes instance

#### `group` (Property with Setter)
Gets or sets the route group name.

**Getter Returns:** Group name string

**Setter Parameters:**
- `value`: Group name string

**Validation:**
- Processes through get_group() method
- Cannot contain punctuation symbols (except underscore)

**Raises:**
- `ValueError`: If group contains invalid symbols

#### `route` (Property with Setter)
Gets or sets the route URL pattern.

**Getter Returns:** Route URL string

**Setter Parameters:**
- `value`: Route URL string

**Validation:**
- Must start with '/'
- Converted to string if not already

**Raises:**
- `InvalidRouteFormatError`: If route doesn't start with '/'

### Static Methods

#### `paramaters_types() -> dict`
Returns mapping of Python types to OpenAPI parameter types.

**Returns:** Dictionary mapping Python type names to OpenAPI types
```python
{'int': 'integer', 'str': 'string', 'float': 'number'}
```

#### `argument_types() -> dict`
Returns mapping of Python types to OpenAPI argument types (includes collections).

**Returns:** Dictionary mapping Python type names to OpenAPI types
```python
{
    'int': 'integer', 'str': 'string', 'float': 'number',
    'list': 'array', 'dict': 'object', 'set': 'array', 'tuple': 'array'
}
```

#### `get_group(group: str) -> str`
Processes group name, returning default if None provided.

**Parameters:**
- `group`: Group name or None

**Returns:** Processed group name or default group

#### `default_group() -> str`
Returns the default group name.

**Returns:** '__pyweber'

#### `default_method() -> list[str]`
Returns the default HTTP methods.

**Returns:** ['GET']

#### `allowed_methods() -> list[str]`
Returns list of all allowed HTTP methods.

**Returns:** ['GET', 'POST', 'PATCH', 'PUT', 'DELETE', 'HEAD', 'OPTIONS']

### Class Methods

#### `get_callback_parameters(cls, callback: Callable[..., Any]) -> dict`
Extracts parameter information from a callback function.

**Parameters:**
- `callback`: Function to analyze

**Returns:** Dictionary with parameter names as keys and parameter info as values
```python
{
    'param_name': {
        'default': default_value,
        'types': parameter_type
    }
}
```

#### `get_query_parameters(cls, route: str, callback: Callable) -> dict`
Analyzes route and callback to generate OpenAPI parameter specification.

**Parameters:**
- `route`: Route URL pattern with parameters
- `callback`: Callback function to analyze

**Returns:** Dictionary with parameters and body specifications
```python
{
    'parameters': {
        'param_name': {
            'type': 'string',
            'required': True,
            'default': None
        }
    },
    'body': {
        'description': '',
        'required': True,
        'content': {...}
    }
}
```

**Process:**
1. Extracts URL parameters using regex pattern `{\s*(.*?)\s*}`
2. Matches parameters with callback function signature
3. Determines parameter types and requirements
4. Generates request body schema for non-URL parameters

### Magic Methods

#### `__repr__() -> str`
Returns string representation of the Route instance.

**Returns:** Formatted string with key route information

## Usage Examples

### Basic Route Creation
```python
from pyweber.models.routes import Route
from pyweber.utils.types import ContentTypes

# Simple HTML route
route = Route(
    route="/",
    template="<h1>Welcome to PyWeber!</h1>",
    title="Home Page"
)

# API route with JSON response
api_route = Route(
    route="/api/users",
    template={"users": [], "total": 0},
    content_type=ContentTypes.json,
    methods=["GET", "POST"]
)

print(route)
# Route(group=__pyweber, route=/, full_route=/, name=None, methods=['GET'], status_code=200)
```

### Route with Parameters
```python
# Route with URL parameters
user_route = Route(
    route="/users/{user_id}",
    template=lambda user_id: f"<h1>User {user_id}</h1>",
    methods=["GET"]
)

# Route with multiple parameters and types
product_route = Route(
    route="/products/{category}/{product_id}",
    template=get_product_template,
    methods=["GET"],
    callback=get_product_data
)

def get_product_data(category: str, product_id: int):
    return f"Product {product_id} in {category}"
```

### Route with Middleware
```python
def auth_middleware(request):
    if not request.headers.get("Authorization"):
        return Response(content="Unauthorized", status_code=401)
    return None

def logging_middleware(request):
    print(f"Accessing: {request.path}")
    return None

# Protected route with middleware
protected_route = Route(
    route="/admin/dashboard",
    template="<h1>Admin Dashboard</h1>",
    middlewares=[auth_middleware, logging_middleware],
    methods=["GET"]
)
```

### Route Groups
```python
# API routes group
api_users = Route(
    route="/users",
    template=get_users,
    group="api",
    content_type=ContentTypes.json,
    methods=["GET", "POST"]
)

api_posts = Route(
    route="/posts",
    template=get_posts,
    group="api",
    content_type=ContentTypes.json,
    methods=["GET", "POST"]
)

print(api_users.full_route)  # /api/users
print(api_posts.full_route)  # /api/posts
```

### Different Template Types
```python
from pyweber.core.template import Template
from pyweber.core.element import Element

# Template object
template_route = Route(
    route="/template-page",
    template=Template(
        template="<h1>{{title}}</h1>",
        context={"title": "Template Page"}
    )
)

# Element object
element_route = Route(
    route="/element-page",
    template=Element(
        tag="div",
        content="<h1>Element Page</h1>"
    )
)

# Callable template
def dynamic_template(**kwargs):
    return f"<h1>Dynamic content: {kwargs}</h1>"

dynamic_route = Route(
    route="/dynamic/{message}",
    template=dynamic_template
)

# Dictionary (JSON) template
json_route = Route(
    route="/api/status",
    template={"status": "ok", "timestamp": "2024-01-01"},
    content_type=ContentTypes.json
)
```

### Route with Custom Status Codes
```python
# Created response
create_route = Route(
    route="/api/users",
    template=create_user,
    methods=["POST"],
    status_code=201,
    content_type=ContentTypes.json
)

# Not found response
not_found_route = Route(
    route="/missing",
    template="<h1>This page doesn't exist</h1>",
    status_code=404
)

# Redirect response
redirect_route = Route(
    route="/old-page",
    template="<h1>Moved</h1>",
    status_code=301
)
```

### Form Handling Routes
```python
# Form display route
form_route = Route(
    route="/contact",
    template='''
    <form method="POST" action="/contact">
        <input type="text" name="name" placeholder="Name" required>
        <input type="email" name="email" placeholder="Email" required>
        <textarea name="message" placeholder="Message" required></textarea>
        <button type="submit">Send</button>
    </form>
    ''',
    methods=["GET"]
)

# Form processing route
def process_contact(name: str, email: str, message: str):
    # Process form data
    return f"<h1>Thank you {name}!</h1><p>We'll contact you at {email}</p>"

form_handler = Route(
    route="/contact",
    template=process_contact,
    methods=["POST"],
    callback=process_contact
)
```

### File Upload Routes
```python
# File upload form
upload_form = Route(
    route="/upload",
    template='''
    <form method="POST" action="/upload" enctype="multipart/form-data">
        <input type="file" name="file" required>
        <button type="submit">Upload</button>
    </form>
    ''',
    methods=["GET"]
)

# File processing
def handle_upload(file):
    if file:
        return f"<h1>File uploaded: {file.filename}</h1>"
    return "<h1>No file uploaded</h1>"

upload_handler = Route(
    route="/upload",
    template=handle_upload,
    methods=["POST"],
    callback=handle_upload
)
```

### Static File Routes
```python
# CSS file route
css_route = Route(
    route="/static/style.css",
    template="body { background-color: #f0f0f0; }",
    content_type=ContentTypes.css
)

# JavaScript file route
js_route = Route(
    route="/static/app.js",
    template="console.log('PyWeber app loaded');",
    content_type=ContentTypes.js
)

# Image route (serving from file)
def serve_image():
    with open("static/logo.png", "rb") as f:
        return f.read()

image_route = Route(
    route="/static/logo.png",
    template=serve_image,
    content_type=ContentTypes.png
)
```

### Advanced Callback Usage
```python
# Async callback
async def async_handler(user_id: int):
    # Simulate async operation
    await asyncio.sleep(0.1)
    return f"<h1>Async User {user_id}</h1>"

async_route = Route(
    route="/async/{user_id}",
    template=async_handler,
    callback=async_handler
)

# Callback with complex parameters
def complex_handler(
    user_id: int,
    category: str = "general",
    limit: int = 10,
    filters: dict = None
):
    filters = filters or {}
    return {
        "user_id": user_id,
        "category": category,
        "limit": limit,
        "filters": filters
    }

complex_route = Route(
    route="/api/users/{user_id}",
    template=complex_handler,
    callback=complex_handler,
    content_type=ContentTypes.json,
    methods=["GET", "POST"]
)
```

### Error Handling in Routes
```python
def safe_handler(user_id: int):
    try:
        # Some operation that might fail
        user = get_user_from_db(user_id)
        return f"<h1>User: {user.name}</h1>"
    except UserNotFound:
        return "<h1>User not found</h1>", 404
    except Exception as e:
        return f"<h1>Error: {str(e)}</h1>", 500

error_route = Route(
    route="/safe/{user_id}",
    template=safe_handler,
    callback=safe_handler
)
```

### Route Parameter Analysis
```python
def analyze_route_params():
    route = Route(
        route="/api/users/{user_id}/posts/{post_id}",
        template=get_user_post,
        callback=get_user_post
    )

    # Get parameter information
    params = Route.get_query_parameters(
        route.route,
        route.callback
    )

    print("URL Parameters:", params['parameters'])
    print("Request Body:", params['body'])

def get_user_post(user_id: int, post_id: int, include_comments: bool = False):
    return {
        "user_id": user_id,
        "post_id": post_id,
        "include_comments": include_comments
    }
```

## Integration with PyWeber Application

### Adding Routes to Application
```python
from pyweber import Pyweber

app = Pyweber()

# Method 1: Direct route creation
route = Route(
    route="/users/{user_id}",
    template=get_user_template,
    methods=["GET"]
)
app.add_route_object(route)

# Method 2: Using app.add_route (creates Route internally)
app.add_route(
    route="/posts",
    template=get_posts,
    methods=["GET", "POST"],
    content_type=ContentTypes.json
)

# Method 3: Using decorator (creates Route internally)
@app.route("/products/{product_id}", methods=["GET"])
def get_product(product_id: int):
    return f"<h1>Product {product_id}</h1>"
```

### Route Groups in Application
```python
app = Pyweber()

# Create API routes group
api_routes = [
    Route(route="/users", template=get_users, group="api"),
    Route(route="/posts", template=get_posts, group="api"),
    Route(route="/comments", template=get_comments, group="api")
]

app.add_group_routes(api_routes)

# Routes will be available at:
# /api/users
# /api/posts  
# /api/comments
```

## OpenAPI Integration

### Automatic Documentation Generation
```python
def documented_handler(
    user_id: int,
    name: str,
    email: str,
    age: int = 18,
    active: bool = True
):
    """
    Get or update user information.

    This endpoint handles user data retrieval and updates.
    """
    return {
        "user_id": user_id,
        "name": name,
        "email": email,
        "age": age,
        "active": active
    }

# Route with full OpenAPI documentation
documented_route = Route(
    route="/api/users/{user_id}",
    template=documented_handler,
    callback=documented_handler,
    methods=["GET", "POST"],
    content_type=ContentTypes.json,
    title="User Management"
)

# OpenAPI spec will include:
# - Path parameters (user_id)
# - Request body schema (name, email, age, active)
# - Response schema
# - Parameter types and defaults
```

## Best Practices

### Route Organization
```python
# Group related routes
user_routes = [
    Route(route="/", template=list_users, group="users"),
    Route(route="/{user_id}", template=get_user, group="users"),
    Route(route="/{user_id}/edit", template=edit_user, group="users")
]

# Use descriptive names
Route(
    route="/api/users",
    template=get_users_api,
    name="users_api",
    methods=["GET"]
)
```

### Error Handling
```python
def robust_handler(**kwargs):
    try:
        return process_request(**kwargs)
    except ValidationError as e:
        return {"error": str(e)}, 400
    except NotFoundError:
        return {"error": "Resource not found"}, 404
    except Exception as e:
        return {"error": "Internal server error"}, 500

Route(
    route="/api/robust",
    template=robust_handler,
    callback=robust_handler,
    content_type=ContentTypes.json
)
```

### Security
```python
# Authentication middleware
def require_auth(request):
    token = request.headers.get("Authorization")
    if not token or not validate_token(token):
        return Response(
            content={"error": "Unauthorized"},
            status_code=401,
            content_type=ContentTypes.json
        )
    return None

# Protected routes
protected_routes = [
    Route(
        route="/admin/users",
        template=admin_users,
        middlewares=[require_auth]
    ),
    Route(
        route="/api/private",
        template=private_api,
        middlewares=[require_auth],
        content_type=ContentTypes.json
    )
]
```

### Performance
```python
# Cache expensive operations
from functools import lru_cache

@lru_cache(maxsize=100)
def expensive_template(category: str):
    # Expensive operation
    return generate_complex_template(category)

cached_route = Route(
    route="/expensive/{category}",
    template=expensive_template
)

# Use appropriate content types
Route(
    route="/api/data",
    template=get_json_data,
    content_type=ContentTypes.json  # Avoid HTML processing
)
```

## Common Patterns

### RESTful API Routes
```python
# RESTful user resource
user_routes = [
    Route(route="/users", template=list_users, methods=["GET"]),
    Route(route="/users", template=create_user, methods=["POST"]),
    Route(route="/users/{user_id}", template=get_user, methods=["GET"]),
    Route(route="/users/{user_id}", template=update_user, methods=["PUT"]),
    Route(route="/users/{user_id}", template=delete_user, methods=["DELETE"])
]
```

### Form Handling Pattern
```python
# Display form
form_route = Route(
    route="/contact",
    template=contact_form_template,
    methods=["GET"]
)

# Process form
form_handler = Route(
    route="/contact",
    template=process_contact_form,
    methods=["POST"],
    callback=process_contact_form
)
```

### API Versioning
```python
# Version 1 API
v1_routes = [
    Route(route="/users", template=v1_users, group="api/v1"),
    Route(route="/posts", template=v1_posts, group="api/v1")
]

# Version 2 API
v2_routes = [
    Route(route="/users", template=v2_users, group="api/v2"),
    Route(route="/posts", template=v2_posts, group="api/v2")
]
```

## Troubleshooting

### Common Issues

1. **Route not matching**: Ensure route starts with '/'
2. **Method not allowed**: Check methods list includes the HTTP method
3. **Middleware errors**: Verify all middleware functions are callable
4. **Parameter extraction**: Ensure callback parameters match URL parameters
5. **Content type issues**: Set appropriate ContentTypes for response

### Debugging Routes
```python
# Debug route information
route = Route(route="/debug/{param}", template=debug_handler)

print(f"Full route: {route.full_route}")
print(f"Methods: {route.methods}")
print(f"Parameters: {Route.get_query_parameters(route.route, route.callback)}")
print(f"Callback: {route.callback}")
```

The Route class is the foundation of PyWeber's routing system, providing flexible and powerful URL handling with support for parameters, middleware, multiple content types, and automatic OpenAPI documentation generation.
