# StateResult Class Documentation

The `StateResult` class is a dataclass that represents the state of a route processing result, containing template, status code, content type, and other processing information.

## Dependencies

```python
from dataclasses import dataclass
from typing import Any, Callable
from pyweber.utils.types import ContentTypes
```

## StateResult Class

### Dataclass Definition
```python
@dataclass
class StateResult:
```

The StateResult class is implemented as a dataclass for automatic initialization and representation methods.

### Fields

#### `template: Any`
The response template or content.
- Can be any type: Template, Element, string, dict, callable, etc.
- Represents the main content to be processed and returned

#### `status_code: int`
HTTP status code for the response.
- Standard HTTP status codes (200, 404, 500, etc.)
- Used to set the response status

#### `content_type: ContentTypes`
Content type for the response.
- Must be a ContentTypes enum value
- Determines how the response is processed and served

#### `redirect_path: str`
Path for redirects or the current route path.
- Used for redirect operations
- Tracks the current processing path

#### `process_response: bool`
Flag indicating whether to process the response through template engine.
- True: Apply template processing (wrap in HTML template)
- False: Return content as-is

#### `kwargs: dict[str, Any]`
Additional parameters and context data.
- Route parameters extracted from URL
- Additional processing context
- Custom data passed between middleware

#### `callback: Callable[..., Any]`
The callback function associated with the route.
- Original route handler function
- Used for parameter inspection and processing

### Methods

#### `update(**kwargs) -> StateResult`
Updates the StateResult fields and returns self for method chaining.

**Parameters:**
- `template`: New template content (optional)
- `status_code`: New status code (optional)
- `content_type`: New content type (optional)
- `redirect_path`: New redirect path (optional)
- `process_response`: New processing flag (optional)
- `callback`: New callback function (optional)
- `kwargs`: New kwargs dictionary (optional)

**Returns:** Self (StateResult instance) for method chaining

**Behavior:**
- Only updates fields that are provided (not None)
- Preserves existing values for unprovided fields
- Returns self to enable method chaining

## Usage Examples

### Basic StateResult Creation
```python
from pyweber.models.routes import StateResult
from pyweber.utils.types import ContentTypes

# Create initial state result
state = StateResult(
    template="<h1>Hello World</h1>",
    status_code=200,
    content_type=ContentTypes.html,
    redirect_path="/home",
    process_response=True,
    kwargs={},
    callback=None
)

print(state.template)      # "<h1>Hello World</h1>"
print(state.status_code)   # 200
print(state.content_type)  # ContentTypes.html
```

### Updating StateResult
```python
# Update specific fields
updated_state = state.update(
    status_code=404,
    template="<h1>Not Found</h1>"
)

print(updated_state.status_code)  # 404
print(updated_state.template)     # "<h1>Not Found</h1>"
print(updated_state.content_type) # ContentTypes.html (unchanged)

# Method chaining
final_state = state.update(
    template="<h1>Processing</h1>",
    status_code=202
).update(
    process_response=False
)
```

### Route Processing Context
```python
def handle_user_route(user_id: int):
    return f"<h1>User {user_id}</h1>"

# State with route parameters
state = StateResult(
    template=handle_user_route,
    status_code=200,
    content_type=ContentTypes.html,
    redirect_path="/users/123",
    process_response=True,
    kwargs={"user_id": 123},
    callback=handle_user_route
)

# Update with processed template
processed_template = state.callback(**state.kwargs)
state.update(template=processed_template)
```

### Error Handling State
```python
# Initial successful state
success_state = StateResult(
    template="<h1>Success</h1>",
    status_code=200,
    content_type=ContentTypes.html,
    redirect_path="/success",
    process_response=True,
    kwargs={},
    callback=None
)

# Convert to error state
error_state = success_state.update(
    template="<h1>Internal Server Error</h1>",
    status_code=500,
    redirect_path="/error"
)
```

### API Response State
```python
# JSON API response state
api_state = StateResult(
    template={"users": [], "total": 0},
    status_code=200,
    content_type=ContentTypes.json,
    redirect_path="/api/users",
    process_response=False,  # Don't wrap JSON in HTML template
    kwargs={"page": 1, "limit": 10},
    callback=lambda page, limit: {"users": [], "total": 0}
)
```

## Common Use Cases

1. **Route Processing**: Tracking state through route resolution pipeline
2. **Middleware Chain**: Passing state between middleware functions
3. **Error Handling**: Converting successful states to error states
4. **Template Processing**: Determining how to process response content
5. **Redirect Handling**: Managing redirect logic and parameters
6. **API Responses**: Configuring JSON vs HTML responses

## Best Practices

### Immutable Updates
```python
# Good: Use update() method for changes
new_state = original_state.update(status_code=404)

# Avoid: Direct field modification in processing pipeline
# original_state.status_code = 404  # Can cause issues in async contexts
```

### Method Chaining
```python
# Chain updates for multiple changes
final_state = initial_state.update(
    template="<h1>Processing</h1>",
    status_code=202
).update(
    process_response=True
)
```

### Context Preservation
```python
# Preserve important context when updating
updated_state = state.update(
    template=new_template,
    # Keep existing kwargs and callback
    kwargs=state.kwargs,
    callback=state.callback
)
```

### Error State Conversion
```python
def handle_error(state: StateResult, error: Exception):
    return state.update(
        template=f"<h1>Error: {str(error)}</h1>",
        status_code=500,
        process_response=True
    )
```

## Performance Considerations

- StateResult is a lightweight dataclass with minimal overhead
- The update() method creates no copies, modifies in-place
- Method chaining returns self, no object creation
- Suitable for high-frequency route processing

## Thread Safety

- StateResult instances are not thread-safe
- Each request should have its own StateResult instance
- Avoid sharing StateResult instances between concurrent requests
- The update() method modifies the instance in-place