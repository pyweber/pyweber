# RedirectRoute Class Documentation

The `RedirectRoute` class represents a route redirection with a target route, HTTP status code, and optional parameters.

## Dependencies

```python
from pyweber.utils.types import HTTPStatusCode
```

## RedirectRoute Class

### Constructor
```python
def __init__(
    self,
    route: 'Route',
    status_code: int = 302,
    **kwargs
):
```

**Parameters:**
- `route`: Target Route instance to redirect to
- `status_code`: HTTP redirect status code (default: 302)
- `**kwargs`: Additional parameters for the redirect

### Properties

#### `route` (Property with Setter)
The target Route instance for redirection.

**Getter:** Returns the target Route object.

**Setter:** Sets the target route with validation.
- Must be a Route instance
- Raises `TypeError` if not a Route instance

#### `status_code` (Property with Setter)
HTTP status code for the redirect response.

**Getter:** Returns the redirect status code.

**Setter:** Sets the status code with validation.
- Must be a valid redirect status code (3xx)
- Raises `ValueError` if not a valid redirect status code

#### `kwargs` (Property with Setter)
Additional parameters for the redirect.

**Getter:** Returns the kwargs dictionary.

**Setter:** Sets additional parameters with validation.
- Must be a dictionary if provided
- Raises `TypeError` if not a dictionary

### Static Methods

#### `redirected_status_code() -> list[int]`
Returns a list of valid HTTP redirect status codes.

**Returns:** List of status codes that start with '3' (3xx codes)

### Magic Methods

#### `__repr__()`
Returns a string representation of the RedirectRoute.

**Format:** `RedirectRoute(route={route}, status_code={status_code})`

## Usage Examples

### Basic Redirect
```python
from pyweber.models.routes import Route, RedirectRoute

# Create target route
target_route = Route(
    route="/dashboard",
    template="<h1>Dashboard</h1>"
)

# Create redirect route
redirect = RedirectRoute(
    route=target_route,
    status_code=301  # Permanent redirect
)

print(redirect.route.route)      # "/dashboard"
print(redirect.status_code)      # 301
```

### Redirect with Parameters
```python
# Create redirect with additional parameters
redirect_with_params = RedirectRoute(
    route=target_route,
    status_code=302,
    user_id=123,
    source="login"
)

print(redirect_with_params.kwargs)  # {"user_id": 123, "source": "login"}
```

### Temporary vs Permanent Redirects
```python
# Temporary redirect (default)
temp_redirect = RedirectRoute(route=target_route)  # 302

# Permanent redirect
perm_redirect = RedirectRoute(route=target_route, status_code=301)

# See and other redirect
see_other = RedirectRoute(route=target_route, status_code=303)
```

## HTTP Redirect Status Codes

### Common Redirect Codes
- **301**: Moved Permanently
- **302**: Found (Temporary Redirect)
- **303**: See Other
- **307**: Temporary Redirect
- **308**: Permanent Redirect

### Validation
```python
# Get all valid redirect status codes
valid_codes = RedirectRoute.redirected_status_code()
print(valid_codes)  # [301, 302, 303, 307, 308, ...]

# Invalid status code raises ValueError
try:
    invalid_redirect = RedirectRoute(route=target_route, status_code=200)
except ValueError as e:
    print(f"Error: {e}")  # 200 must be an Redirect HttpStatusCode valid
```

## Integration with RouteManager

### Creating Redirects
```python
from pyweber.models.routes import RouteManager

route_manager = RouteManager()

# Add target route
route_manager.add_route("/new-page", template="<h1>New Page</h1>")

# Create redirect using RouteManager
redirect_route = route_manager.to_route("/new-page", status_code=301)

# Add redirect mapping
route_manager.redirect(
    from_route="/old-page",
    target="/new-page",
    status_code=301
)
```

### Redirect Resolution
```python
# Check if route is redirected
if route_manager.is_redirected("/old-page"):
    redirect = route_manager.get_redirected_route("/old-page")
    print(f"Redirects to: {redirect.route.route}")
    print(f"Status code: {redirect.status_code}")
```

## Error Handling

### Type Validation
```python
try:
    # Invalid route type
    invalid_redirect = RedirectRoute(route="not-a-route")
except TypeError as e:
    print(f"Type error: {e}")

try:
    # Invalid kwargs type
    redirect = RedirectRoute(route=target_route)
    redirect.kwargs = "not-a-dict"
except TypeError as e:
    print(f"Type error: {e}")
```

### Status Code Validation
```python
try:
    # Invalid status code
    invalid_redirect = RedirectRoute(route=target_route, status_code=404)
except ValueError as e:
    print(f"Value error: {e}")
```

## Common Use Cases

1. **URL Migration**: Redirecting old URLs to new ones
2. **Authentication Flow**: Redirecting after login/logout
3. **Canonical URLs**: Enforcing preferred URL formats
4. **Temporary Maintenance**: Redirecting during maintenance
5. **A/B Testing**: Redirecting users to different versions

## Best Practices

### Choose Appropriate Status Codes
```python
# Permanent URL changes
permanent_redirect = RedirectRoute(route=new_route, status_code=301)

# Temporary redirects
temporary_redirect = RedirectRoute(route=temp_route, status_code=302)

# POST redirect pattern
post_redirect = RedirectRoute(route=success_route, status_code=303)
```

### Parameter Passing
```python
# Pass context through redirect
context_redirect = RedirectRoute(
    route=dashboard_route,
    status_code=302,
    message="Login successful",
    user_type="admin"
)
```

### Chain Prevention
```python
# Avoid redirect chains - redirect directly to final destination
# Bad: /old -> /intermediate -> /final
# Good: /old -> /final
final_redirect = RedirectRoute(route=final_route, status_code=301)
```

## SEO Considerations

- **301 redirects**: Pass link equity to new URL
- **302 redirects**: Temporary, don't pass full link equity
- **Avoid redirect chains**: Can dilute SEO value
- **Update internal links**: Don't rely solely on redirects