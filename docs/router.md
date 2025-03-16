# Routing in PyWeber

The routing system in PyWeber connects URLs to templates, allowing you to create a navigable web application with multiple pages.

## Basic Routing

### Adding Routes

The most common way to add routes is through the `add_route` method:

```python
import pyweber as pw

class HomePage(pw.Template):
    def __init__(self, app: pw.Router):
        super().__init__(template="home.html")
        # Template setup...

class AboutPage(pw.Template):
    def __init__(self, app: pw.Router):
        super().__init__(template="about.html")
        # Template setup...

def main(app: pw.Router):
    # Basic route
    app.add_route("/", template=HomePage(app=app))

    # Another route
    app.add_route("/about", template=AboutPage(app=app))

if __name__ == "__main__":
    pw.run(target=main)
```

### Route Decorator

You can also use the `route` decorator for a more Flask-like syntax:

```python
def main(app: pw.Router):
    @app.route("/")
    def home():
        return HomePage(app=app)

    @app.route("/about")
    def about():
        return AboutPage(app=app)
```

## Dynamic Routes

PyWeber supports dynamic routes with parameters:

```python
class UserProfile(pw.Template):
    def __init__(self, app: pw.Router, user_id=None):
        super().__init__(template="user_profile.html")
        self.user_id = user_id
        self.title = self.querySelector("h1")
        self.title.content = f"User Profile: {user_id}"

def main(app: pw.Router):
    # Dynamic route with parameter
    app.add_route("/users/{user_id}", template=UserProfile(app=app))
```

## Router API

### Constructor


Router(update_handler: callable)


- `update_handler`: A function that handles template updates

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `list_routes` | list[str] | List of all registered routes |
| `clear_routes` | None | Clears all registered routes |
| `page_not_found` | Template | Template for 404 errors |
| `page_unauthorized` | Template | Template for 401 errors |
| `cookies` | list[str] | List of cookies to be sent with responses |

### Methods

#### add_route

```python
add_route(route: str, template: Template) -> None
```

Adds a new route to the application.

- `route`: URL path (must start with `/`)
- `template`: Template instance to render for this route

#### update_route

```python
update_route(route: str, template: Template) -> None
```

Updates an existing route with a new template.

- `route`: Existing URL path
- `template`: New template instance

#### remove_route

```python
remove_route(route: str) -> None
```

Removes a route from the application.

- `route`: URL path to remove

#### redirect

```python
redirect(from_route: str, to_route: str) -> None
```

Creates a redirect from one route to another.

- `from_route`: Source URL path
- `to_route`: Destination URL path (must exist)

#### get_template

```python
get_template(route: str) -> Template
```

Gets the template for a specific route.

- `route`: URL path
- Returns: Template instance or 404 template if not found

#### exists

```python
exists(route: str) -> bool
```

Checks if a route exists.

- `route`: URL path to check
- Returns: True if the route exists, False otherwise

#### is_redirected

```python
is_redirected(route: str) -> bool
```

Checks if a route is redirected.

- `route`: URL path to check
- Returns: True if the route is redirected, False otherwise

#### set_cookie

```python
set_cookie(
    cookie_name: str,
    cookie_value: str,
    path: str = '/',
    samesite: str = 'Strict',
    httponly: bool = True,
    secure: bool = True,
    expires: datetime = None
) -> None
```

Sets a cookie to be sent with responses.

- `cookie_name`: Name of the cookie
- `cookie_value`: Value of the cookie
- `path`: Cookie path (default: '/')
- `samesite`: SameSite attribute (options: 'Strict', 'Lax', None)
- `httponly`: Whether the cookie is HTTP-only (default: True)
- `secure`: Whether the cookie requires HTTPS (default: True)
- `expires`: Expiration date (default: None, session cookie)

#### launch_url

```python
launch_url(url: str) -> bool
```

Opens a URL in the default web browser.

- `url`: URL to open
- Returns: True if successful, False otherwise

## Middleware

Middleware functions process requests before they reach the template. They can modify requests, perform authentication, or return alternative responses.

### Adding Middleware

```python
def auth_middleware(request: pw.Request):
    # Check if user is authenticated
    if 'user_id' not in request.cookies:
        # Return unauthorized template
        return UnauthorizedTemplate()
    return None  # Continue to the next middleware or route handler

def main(app: pw.Router):
    # Add middleware to the router
    app.middleware(auth_middleware)

    # Or use as a decorator
    @app.middleware
    def log_requests(request: pw.Request):
        print(f"Request: {request.method} {request.path}")
        return None  # Continue processing
```

### Middleware Flow

1. When a request is received, each middleware function is called in order
2. If a middleware returns a Template, that template is rendered and no further processing occurs
3. If all middleware return None, the router processes the request normally

## Request Object

The Request object contains information about the incoming HTTP request.

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `method` | str | HTTP method (GET, POST, etc.) |
| `path` | str | URL path |
| `netloc` | str | Network location (domain) |
| `host` | str | Host header value |
| `user_agent` | str | User-Agent header value |
| `cookies` | dict[str, str] | Dictionary of cookies |
| `referer` | str | Referer header value |
| `accept` | list[str] | Accept header values |
| `params` | dict[str, str] | URL query parameters |
| `fragment` | str | URL fragment (after #) |

## Response Handling

PyWeber automatically builds HTTP responses based on templates and their status codes.

### Status Codes

You can set custom status codes for templates:

```python
# Create a template with a specific status code
error_template = pw.Template(template="error.html", status_code=500)

# Or change the status code later
template.status_code = 201  # Created
```

### Content Types

PyWeber automatically determines the appropriate content type based on the requested file extension:

- `.html` → `text/html`
- `.css` → `text/css`
- `.js` → `application/javascript`
- `.json` → `application/json`
- `.png`, `.jpg`, `.gif` → appropriate image types
- etc.

## Error Handling

PyWeber provides default templates for common errors:

### 404 Not Found

By default, PyWeber shows a simple 404 page when a route is not found. You can customize this:

```python
def main(app: pw.Router):
    # Create a custom 404 template
    custom_404 = pw.Template(template="404.html", status_code=404)

    # Set it as the default not found page
    app.page_not_found = custom_404
```

### 401 Unauthorized

Similarly, you can customize the unauthorized page:

```python
def main(app: pw.Router):
    # Create a custom 401 template
    custom_401 = pw.Template(template="401.html", status_code=401)

    # Set it as the default unauthorized page
    app.page_unauthorized = custom_401
```

## Advanced Routing

### Serving Static Files

PyWeber automatically serves static files from the appropriate directories:


```bash
my_project/
├── main.py
├── templates/
│   └── index.html
└── src/
    ├── style/
    │   └── style.css
    └── assets/
        └── logo.png
```

These files are accessible at:
- `/src/style/style.css`
- `/src/assets/logo.png`

### External Requests

PyWeber can proxy requests to external URLs:

```python
def main(app: pw.Router):
    # This will proxy requests to /api/* to the external API
    app.add_route("/api", template=ExternalAPIProxy(app=app))
```

## Example: Complete Routing Setup

```python
import pyweber as pw
from datetime import datetime, timedelta

class HomePage(pw.Template):
    def __init__(self, app: pw.Router):
        super().__init__(template="home.html")
        # Template setup...

class LoginPage(pw.Template):
    def __init__(self, app: pw.Router):
        super().__init__(template="login.html")
        self.form = self.querySelector("form")
        self.username = self.querySelector("#username")
        self.password = self.querySelector("#password")
        self.error = self.querySelector(".error")

        self.form.events.onsubmit = self.handle_login

    def handle_login(self, e: pw.EventHandler):
        username = self.username.value
        password = self.password.value

        # Simple authentication (in a real app, use proper auth)
        if username == "admin" and password == "password":
            # Set authentication cookie
            app.set_cookie(
                cookie_name="user_id",
                cookie_value="admin",
                expires=datetime.now() + timedelta(days=7)
            )

            # Redirect to dashboard
            return app.redirect("/login", "/dashboard")
        else:
            self.error.content = "Invalid username or password"

class DashboardPage(pw.Template):
    def __init__(self, app: pw.Router):
        super().__init__(template="dashboard.html")
        # Template setup...

def auth_middleware(request: pw.Request):
    # Protected routes
    protected_routes = ["/dashboard", "/profile", "/settings"]

    # Check if the requested path is protected
    if request.path in protected_routes:
        # Check if user is authenticated
        if 'user_id' not in request.cookies:
            # Return unauthorized template
            return app.page_unauthorized

    # Continue processing
    return None

def main(app: pw.Router):
    # Add middleware
    app.middleware(auth_middleware)

    # Add routes
    app.add_route("/", template=HomePage(app=app))
    app.add_route("/login", template=LoginPage(app=app))
    app.add_route("/dashboard", template=DashboardPage(app=app))

    # Add redirects
    app.redirect("/home", "/")
    app.redirect("/admin", "/dashboard")

    # Custom error pages
    app.page_not_found = pw.Template(template="404.html", status_code=404)
    app.page_unauthorized = pw.Template(template="401.html", status_code=401)

if __name__ == "__main__":
    pw.run(target=main)
```

## Best Practices

1. **Organize Routes**: Group related routes together
2. **Use Descriptive Names**: Make route paths descriptive and follow REST conventions
3. **Protect Sensitive Routes**: Use middleware for authentication and authorization
4. **Custom Error Pages**: Create user-friendly error pages
5. **Redirects**: Use redirects for moved content or friendly URLs
6. **Stateless Design**: Keep routes stateless when possible
7. **Parameter Validation**: Validate route parameters before using them

## Next Steps

- Learn about [Templates](template.md) for creating dynamic pages
- Explore [Elements](elements.md) for manipulating the DOM
- Understand [Event Handling](events.md) for interactive applications