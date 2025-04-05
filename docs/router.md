
# PyWeber Core

The PyWeber class is the central component of the PyWeber framework, handling routing, request processing, and template management.

## Basic Usage
```python
import pyweber as pw

class HomePage(pw.Template):
    def __init__(self, app: pw.Pyweber):
        super().__init__(template="home.html")
        # Template setup...

def main(app: pw.Pyweber):
    app.add_route("/", template=HomePage(app=app))

if __name__ == "__main__":
    pw.run(target=main)
```
## Initialization
```python
app = pw.Pyweber()
```
The PyWeber constructor accepts optional keyword arguments:
- `update_handler`: A function that handles template updates

## Routing

### Adding Routes
```python
# Add a route with a template
app.add_route("/", template=HomePage(app=app))

# Add a route with a function that returns a template
app.add_route("/dynamic", template=get_dynamic_page)

# Add a route with a dictionary (returns JSON)
app.add_route("/api/data", template={"name": "John", "age": 30})

# Add a route with a string (converted to a template)
app.add_route("/simple", template="<h1>Simple Page</h1>")
```

### Route Decorator
```python
@app.route("/users")
def users_page(app=app):
    return UsersPage(app=app)

# With dynamic parameters
@app.route("/users/{user_id}")
def user_profile(user_id, app=app):
    return UserProfile(app=app, user_id=user_id)
```

### Managing Routes
```python
# Update an existing route
app.update_route("/", template=NewHomePage(app=app))

# Remove a route
app.remove_route("/old-page")

# Create a redirect
app.redirect("/old-path", "/new-path")

# Check if a route exists
if app.exists("/about"):
    print("About page exists")

# Check if a route is redirected
if app.is_redirected("/old-path"):
    print("This path is redirected")

# Get all routes
routes = app.list_routes

# Clear all routes
app.clear_routes
```

## Middleware

PyWeber supports middleware for processing requests before and after they reach the route handler.

### Before Request Middleware
```python
@app.before_request(status_code=200)
def auth_middleware(request: pw.Request):
    # Check if user is authenticated
    if 'user_id' not in request.cookies:
        # Return unauthorized template
        return app.page_unauthorized

    # Continue processing
    return None
```

### After Request Middleware
```python
@app.after_request()
def log_response(response: pw.Response):
    # Log response details
    print(f"Response: {response.code} {response.route}")

    # Modify response if needed
    response.add_header("X-Custom-Header", "Value")

    return response
```

### Clearing Middleware
```python
# Clear before request middleware
app.clear_before_request

# Clear after request middleware
app.clear_after_request

## Error Pages

PyWeber provides default error pages that can be customized:

# Custom 404 page
app.page_not_found = pw.Template(template="404.html", status_code=404)

# Custom 401 page
app.page_unauthorized = pw.Template(template="401.html", status_code=401)

# Custom 500 page
app.page_server_error = pw.Template(template="500.html", status_code=500)
```
## Cookie Management
```python
# Set a cookie
app.set_cookie(
    cookie_name="user_id",
    cookie_value="12345",
    path="/",
    samesite="Strict",
    httponly=True,
    secure=True,
    expires=None  # Session cookie
)

# Get all cookies
cookies = app.cookies

## Template Management

# Get a template for a specific route
template = app.clone_template("/about")

# Update the template
template.querySelector("h1").content = "New Title"

# Update the route with the modified template
app.update_route("/about", template=template)
```

## Browser Integration
```python
# Open a URL in the default browser
app.launch_url("https://example.com")
```

## Window API

PyWeber provides a Window API for browser-like functionality:

```python
# Access the window object
window = app.window

# Set window title
window.title = "My PyWeber App"

# Set window location
window.location = "/dashboard"

# Add window event handler
window.events.onresize = handle_resize
```

## ASGI Support

PyWeber can be used with ASGI servers like Uvicorn:

```python
# app.py
import pyweber as pw

class HomePage(pw.Template):
    def __init__(self, app: pw.Pyweber):
        super().__init__(template="home.html")

def setup_routes(app: pw.Pyweber):
    app.add_route("/", template=HomePage(app=app))
setup_routes(app)

# Run with uvicorn
# uvicorn app:app
```
## Example: Complete Application
```python
import pyweber as pw
from datetime import datetime, timedelta

class HomePage(pw.Template):
    def __init__(self, app: pw.Pyweber):
        super().__init__(template="home.html")
        self.title = self.querySelector("h1")
        self.login_button = self.querySelector("#login-button")
        self.login_button.events.onclick = self.go_to_login

    def go_to_login(self, e: pw.EventHandler):
        app.window.location = "/login"
        e.update()

class LoginPage(pw.Template):
    def __init__(self, app: pw.Pyweber):
        super().__init__(template="login.html")
        self.form = self.querySelector("form")
        self.username = self.querySelector("#username")
        self.password = self.querySelector("#password")
        self.error = self.querySelector(".error")
        self.form.events.onsubmit = self.handle_login

    def handle_login(self, e: pw.EventHandler):
        username = self.username.value
        password = self.password.value

        if username == "admin" and password == "password":
            # Set authentication cookie
            app.set_cookie(
                cookie_name="user_id",
                cookie_value="admin",
                expires=datetime.now() + timedelta(days=7)
            )

            # Redirect to dashboard
            app.window.location = "/dashboard"
        else:
            self.error.content = "Invalid username or password"

        e.update()

class DashboardPage(pw.Template):
    def __init__(self, app: pw.Pyweber):
        super().__init__(template="dashboard.html")
        self.welcome = self.querySelector("#welcome")
        self.logout = self.querySelector("#logout")
        self.logout.events.onclick = self.handle_logout

    def handle_logout(self, e: pw.EventHandler):
        # Clear cookie by setting it to expire in the past
        app.set_cookie(
            cookie_name="user_id",
            cookie_value="",
            expires=datetime(1970, 1, 1)
        )

        # Redirect to home
        app.window.location = "/"
        e.update()

@app.before_request()
def auth_middleware(request: pw.Request):
    # Protected routes
    protected_routes = ["/dashboard"]

    # Check if the requested path is protected
    if request.path in protected_routes:
        # Check if user is authenticated
        if 'user_id' not in request.cookies:
            # Return unauthorized template
            return app.page_unauthorized

    # Continue processing
    return None

def main(app: pw.Pyweber):
    # Add routes
    app.add_route("/", template=HomePage(app=app))
    app.add_route("/login", template=LoginPage(app=app))
    app.add_route("/dashboard", template=DashboardPage(app=app))

    # Add redirects
    app.redirect("/home", "/")

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
5. **Stateless Design**: Keep routes stateless when possible
6. **Parameter Validation**: Validate route parameters before using them

## Next Steps

- Learn about [Templates](template.md) for creating dynamic pages
- Explore [Elements](element.md) for manipulating the DOM
- Understand [Event Handling](events.md) for interactive applications