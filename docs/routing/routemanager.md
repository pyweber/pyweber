# RouteManager

The `RouteManager` class manages web routes, redirects, and route resolution for the PyWeber framework.

## Dependencies

```python
import inspect
from typing import Union, Callable, Any
from pyweber.core.element import Element
from pyweber.core.template import Template
from pyweber.utils.types import ContentTypes
from pyweber.utils.exceptions import (
    RouteAlreadyExistError,
    RouteNotFoundError,
    RouteNameAlreadyExistError
)
```

## RouteManager Class

### Constructor
```python
def __init__(self):
```

Initializes an empty route manager with internal storage for routes, redirects, and route names.

### Properties

#### `default_group`
Returns the default route group name.

**Returns:** `'__pyweber'`

#### `list_routes`
Returns a list of public route paths (excludes internal PyWeber routes).

**Returns:** List of route paths as strings

#### `list_redirected_routes`
Returns a list of all redirected route paths.

**Returns:** List of redirected route paths

### Route Management Methods

#### `add_route(route: str, template: Union[Callable, Template, Element, str, dict], **kwargs)`
Adds a new route to the manager.

**Parameters:**
- `route`: URL pattern for the route
- `template`: Response template or handler
- `methods`: HTTP methods (optional)
- `group`: Route group (optional)
- `name`: Route name (optional)
- `middlewares`: Middleware functions (optional)
- `status_code`: HTTP status code (optional)
- `content_type`: Response content type (optional)
- `title`: Page title (optional)
- `process_response`: Template processing flag (optional)

**Raises:**
- `RouteAlreadyExistError`: If route already exists
- `RouteNameAlreadyExistError`: If route name already exists

#### `add_group_routes(routes: list[Route], group: str = None)`
Adds multiple routes to a specific group.

**Parameters:**
- `routes`: List of Route instances
- `group`: Target group name

**Raises:**
- `TypeError`: If any item is not a Route instance

#### `update_route(route: str, group: str = None, **kwargs)`
Updates an existing route's properties.

**Parameters:**
- `route`: Route path to update
- `group`: Route group
- `**kwargs`: Properties to update

**Raises:**
- `RouteNotFoundError`: If route doesn't exist
- `ValueError`: If new name conflicts with existing route

#### `remove_route(route: str, group: str = None)`
Removes a route from the manager.

**Parameters:**
- `route`: Route path to remove
- `group`: Route group

#### `remove_group(group: str)`
Removes all routes in a specific group.

**Parameters:**
- `group`: Group name to remove

#### `clear_routes()`
Removes all public routes (keeps internal PyWeber routes).

### Route Retrieval Methods

#### `get_route_by_path(route: str, follow_redirect: bool = True) -> Route`
Retrieves a route by its path.

**Parameters:**
- `route`: Route path
- `follow_redirect`: Whether to follow redirects

**Returns:** Route instance or None

#### `get_route_by_name(name: str) -> Route`
Retrieves a route by its name.

**Parameters:**
- `name`: Route name

**Returns:** Route instance or None

#### `get_group_routes(group: str = None) -> list[Route]`
Gets all routes in a specific group.

**Parameters:**
- `group`: Group name

**Returns:** List of Route instances

#### `route_info(target: str) -> Route`
Gets route information by name or path.

**Parameters:**
- `target`: Route name or path

**Returns:** Route instance or None

### Redirect Management

#### `redirect(from_route: str, target: str, status_code: int = 302, **kwargs)`
Creates a redirect from one route to another.

**Parameters:**
- `from_route`: Source route path
- `target`: Target route name or path
- `status_code`: HTTP redirect status code
- `**kwargs`: Additional redirect parameters

**Raises:**
- `RouteNotFoundError`: If target route doesn't exist
- `ValueError`: If status code is not a valid redirect code

#### `to_route(target: str, status_code: int = 302, **kwargs) -> RedirectRoute`
Creates a RedirectRoute object for programmatic redirects.

**Parameters:**
- `target`: Target route name or path
- `status_code`: HTTP redirect status code
- `**kwargs`: Additional redirect parameters

**Returns:** RedirectRoute instance

**Raises:**
- `RouteNotFoundError`: If target route doesn't exist
- `ValueError`: If status code is not a valid redirect code

#### `is_redirected(route: str) -> bool`
Checks if a route is redirected.

**Parameters:**
- `route`: Route path to check

**Returns:** True if route is redirected

#### `get_redirected_route(route: str) -> RedirectRoute`
Gets the redirect information for a route.

**Parameters:**
- `route`: Route path

**Returns:** RedirectRoute instance or None

#### `remove_redirected_route(route: str)`
Removes a redirect mapping.

**Parameters:**
- `route`: Route path to remove redirect for

### Route Resolution

#### `exists(route: str) -> bool`
Checks if a route exists (including redirects).

**Parameters:**
- `route`: Route path to check

**Returns:** True if route exists

#### `resolve_path(route: str) -> tuple[str, dict[str, str]]`
Resolves a route path and extracts parameters.

**Parameters:**
- `route`: Route path to resolve

**Returns:** Tuple of (resolved_path, parameters_dict)

#### `full_route(route: str, group: str) -> str`
Constructs the full route path including group.

**Parameters:**
- `route`: Route path
- `group`: Group name

**Returns:** Full route path

### Decorator Method

#### `route(route: str, **kwargs)`
Decorator for registering route handlers.

**Parameters:**
- `route`: URL pattern
- `methods`: HTTP methods (optional)
- `group`: Route group (optional)
- `name`: Route name (optional)
- `middlewares`: Middleware functions (optional)
- `status_code`: HTTP status code (optional)
- `content_type`: Response content type (optional)
- `title`: Page title (optional)
- `process_response`: Template processing flag (optional)

**Returns:** Decorator function

### Utility Methods

#### `get_group(group: str) -> str`
Gets group name or returns default.

**Parameters:**
- `group`: Group name

**Returns:** Group name or default group

#### `get_group_by_route(route: str) -> str`
Gets the group name for a specific route.

**Parameters:**
- `route`: Route path

**Returns:** Group name or None

#### `get_group_and_route(route: str) -> tuple[str, str]`
Splits a full route into group and route components.

**Parameters:**
- `route`: Full route path

**Returns:** Tuple of (group, route)

#### `build_route(route: str, **kwargs) -> str`
Builds a route URL with parameter substitution.

**Parameters:**
- `route`: Route pattern with placeholders
- `**kwargs`: Parameter values

**Returns:** Built route URL

### Static Methods

#### `validate_callable_args(callback: Callable, **kwargs) -> dict`
Validates and prepares arguments for a callable.

**Parameters:**
- `callback`: Function to validate arguments for
- `**kwargs`: Arguments to validate

**Returns:** Dictionary of validated arguments

#### `inspect_function(callback: Callable) -> list[dict]`
Inspects a function's signature and parameters.

**Parameters:**
- `callback`: Function to inspect

**Returns:** List of parameter information dictionaries

## Usage Examples

### Basic Route Management
```python
from pyweber.models.routes import RouteManager
from pyweber.utils.types import ContentTypes

# Create route manager
manager = RouteManager()

# Add simple route
manager.add_route(
    route="/home",
    template="<h1>Welcome Home</h1>",
    name="home_page",
    title="Home"
)

# Add API route
manager.add_route(
    route="/api/users",
    template=lambda: {"users": []},
    methods=["GET", "POST"],
    content_type=ContentTypes.json,
    group="api"
)

# Check if route exists
if manager.exists("/home"):
    print("Home route exists")

# Get route by name
home_route = manager.get_route_by_name("home_page")
print(home_route.route)  # "/home"
```

### Using the Route Decorator
```python
# Create route manager instance
manager = RouteManager()

# Use decorator to register routes
@manager.route("/users/{user_id}", methods=["GET"], name="user_detail")
def get_user(user_id: int):
    return f"<h1>User {user_id}</h1>"

@manager.route("/api/posts", methods=["GET", "POST"], 
               content_type=ContentTypes.json, group="api")
async def handle_posts():
    return {"posts": []}

# Routes are automatically registered
user_route = manager.get_route_by_name("user_detail")
print(user_route.full_route)  # "/users/{user_id}"
```

### Route Groups
```python
from pyweber.models.routes import Route

# Create routes for a group
api_routes = [
    Route(route="/users", template=lambda: {"users": []}),
    Route(route="/posts", template=lambda: {"posts": []}),
    Route(route="/comments", template=lambda: {"comments": []})
]

# Add all routes to API group
manager.add_group_routes(api_routes, group="api")

# Get all routes in the API group
api_group_routes = manager.get_group_routes("api")
for route in api_group_routes:
    print(route.full_route)  # /api/users, /api/posts, /api/comments
```

### Redirects
```python
# Add target route
manager.add_route("/new-page", template="<h1>New Page</h1>", name="new_page")

# Create redirect from old URL to new URL
manager.redirect(
    from_route="/old-page",
    target="new_page",  # Can use route name
    status_code=301     # Permanent redirect
)

# Alternative: redirect to route path
manager.redirect(
    from_route="/another-old-page",
    target="/new-page",  # Direct path
    status_code=302      # Temporary redirect
)

# Check if route is redirected
if manager.is_redirected("/old-page"):
    redirect = manager.get_redirected_route("/old-page")
    print(f"Redirects to: {redirect.route.route}")
    print(f"Status: {redirect.status_code}")
```

### Programmatic Redirects
```python
# Create redirect route object
def login_required():
    # Check authentication
    if not user_authenticated():
        return manager.to_route("login_page", status_code=302)
    return "<h1>Protected Content</h1>"

manager.add_route("/protected", template=login_required)
```

### Route Parameters
```python
# Route with parameters
@manager.route("/users/{user_id}/posts/{post_id}")
def get_user_post(user_id: int, post_id: int):
    return f"User {user_id}, Post {post_id}"

# Resolve route with parameters
path, params = manager.resolve_path("/users/123/posts/456")
print(path)    # "/users/{user_id}/posts/{post_id}"
print(params)  # {"user_id": "123", "post_id": "456"}

# Build route with parameters
built_route = manager.build_route("/users/{user_id}/posts/{post_id}", 
                                  user_id=123, post_id=456)
print(built_route)  # "/users/123/posts/456"
```

### Route Updates
```python
# Add initial route
manager.add_route("/example", template="Original content")

# Update route properties
manager.update_route(
    route="/example",
    template="Updated content",
    title="Updated Title",
    status_code=200
)

# Update with new name
manager.update_route(
    route="/example",
    name="example_page"
)
```

### Route Removal
```python
# Remove specific route
manager.remove_route("/unwanted-route")

# Remove entire group
manager.remove_group("deprecated_api")

# Clear all public routes (keeps internal routes)
manager.clear_routes()
```

## Error Handling

### Route Conflicts
```python
try:
    manager.add_route("/duplicate", template="First")
    manager.add_route("/duplicate", template="Second")
except RouteAlreadyExistError:
    print("Route already exists")

try:
    manager.add_route("/first", template="Content", name="same_name")
    manager.add_route("/second", template="Content", name="same_name")
except RouteNameAlreadyExistError:
    print("Route name already exists")
```

### Missing Routes
```python
try:
    manager.redirect("/from", "/nonexistent", status_code=301)
except RouteNotFoundError:
    print("Target route not found")

try:
    manager.update_route("/nonexistent", title="New Title")
except RouteNotFoundError:
    print("Route to update not found")
```

### Invalid Redirects
```python
try:
    manager.redirect("/from", "/to", status_code=200)  # Not a redirect code
except ValueError:
    print("Invalid redirect status code")
```

## Integration with PyWeber

### Framework Integration
```python
from pyweber import Pyweber

# PyWeber inherits from RouteManager
app = Pyweber()

# All RouteManager methods available
app.add_route("/", template="<h1>Home</h1>")

@app.route("/about")
def about():
    return "<h1>About Us</h1>"

# Route resolution during request handling
route = app.get_route_by_path("/about")
```

### Middleware Integration
```python
def auth_middleware(request):
    # Authentication logic
    pass

# Add route with middleware
manager.add_route(
    route="/admin",
    template="<h1>Admin Panel</h1>",
    middlewares=[auth_middleware]
)
```

## Common Use Cases

1. **Web Applications**: Managing page routes and API endpoints
2. **URL Migration**: Handling redirects from old to new URLs
3. **API Versioning**: Organizing routes by version groups
4. **Authentication**: Protecting routes with middleware
5. **Content Management**: Dynamic route registration
6. **Microservices**: Route organization and management

## Performance Considerations

- Route resolution uses pattern matching for parameters
- Large numbers of routes may impact resolution performance
- Group organization helps with route management
- Redirect chains should be avoided for performance

## Best Practices

### Route Organization
```python
# Use groups for logical organization
manager.add_group_routes(auth_routes, group="auth")
manager.add_group_routes(api_v1_routes, group="api/v1")
manager.add_group_routes(admin_routes, group="admin")
```

### Named Routes
```python
# Use names for important routes
manager.add_route("/", template="Home", name="home")
manager.add_route("/contact", template="Contact", name="contact")

# Reference by name in redirects
manager.redirect("/old-contact", "contact", status_code=301)
```

### Parameter Validation
```python
@manager.route("/users/{user_id}")
def get_user(user_id: int):  # Type hints help with validation
    if user_id <= 0:
        raise ValueError("Invalid user ID")
    return f"User {user_id}"
```