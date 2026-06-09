# TemplateResult Class Documentation

The `TemplateResult` class is a dataclass that represents the result of template processing, containing the processed content, status code, content type, and additional metadata.

## Dependencies

```python
from dataclasses import dataclass
from typing import Any
from pyweber.utils.types import ContentTypes
```

## TemplateResult Class

### Dataclass Definition
```python
@dataclass
class TemplateResult:
```

The TemplateResult class is implemented as a dataclass for automatic initialization and representation methods.

### Fields

#### `content: Any`
The processed template content ready for response.
- Can be string (HTML, CSS, JS), dict (JSON), bytes, or other content types
- Represents the final processed output to be sent to the client

#### `status_code: int`
HTTP status code for the response.
- Standard HTTP status codes (200, 404, 500, etc.)
- Determines the response status sent to the client

#### `content_type: ContentTypes`
Content type for the response.
- Must be a ContentTypes enum value
- Determines the Content-Type header and response processing

#### `kwargs: dict[str, Any]`
Additional metadata and context information.
- Processing context data
- Template variables and parameters
- Custom metadata for response handling

### Methods

#### `update(**kwargs) -> TemplateResult`
Updates the TemplateResult fields and returns self for method chaining.

**Parameters:**
- `content`: New processed content (optional)
- `status_code`: New status code (optional)
- `content_type`: New content type (optional)
- `kwargs`: New kwargs dictionary (optional)

**Returns:** Self (TemplateResult instance) for method chaining

**Behavior:**
- Only updates fields that are provided (not None)
- Preserves existing values for unprovided fields
- Returns self to enable method chaining

## Usage Examples

### Basic TemplateResult Creation
```python
from pyweber.models.routes import TemplateResult
from pyweber.utils.types import ContentTypes

# Create HTML template result
html_result = TemplateResult(
    content="<html><body><h1>Hello World</h1></body></html>",
    status_code=200,
    content_type=ContentTypes.html,
    kwargs={"title": "Hello World", "user": "John"}
)

print(html_result.content)      # Full HTML content
print(html_result.status_code)  # 200
print(html_result.content_type) # ContentTypes.html
```

### JSON API Response
```python
# Create JSON template result
json_result = TemplateResult(
    content={"users": [{"id": 1, "name": "John"}], "total": 1},
    status_code=200,
    content_type=ContentTypes.json,
    kwargs={"page": 1, "limit": 10}
)

print(json_result.content)  # Dictionary with user data
```

### Error Response
```python
# Create error template result
error_result = TemplateResult(
    content="<html><body><h1>404 - Page Not Found</h1></body></html>",
    status_code=404,
    content_type=ContentTypes.html,
    kwargs={"error_type": "not_found", "requested_path": "/missing"}
)
```

### CSS/JS Static Content
```python
# CSS template result
css_result = TemplateResult(
    content="body { margin: 0; padding: 20px; font-family: Arial; }",
    status_code=200,
    content_type=ContentTypes.css,
    kwargs={"minified": False}
)

# JavaScript template result
js_result = TemplateResult(
    content="console.log('Hello from PyWeber');",
    status_code=200,
    content_type=ContentTypes.javascript,
    kwargs={"version": "1.0"}
)
```

### Updating TemplateResult
```python
# Update specific fields
updated_result = html_result.update(
    status_code=201,
    content="<html><body><h1>Created Successfully</h1></body></html>"
)

print(updated_result.status_code)  # 201
print(updated_result.content_type) # ContentTypes.html (unchanged)

# Method chaining
final_result = html_result.update(
    content="<h1>Processing</h1>",
    status_code=202
).update(
    kwargs={"processing": True}
)
```

## Common Use Cases

1. **Web Pages**: HTML content with full page templates
2. **API Responses**: JSON data with proper status codes
3. **Static Files**: CSS, JS, images with appropriate content types
4. **File Downloads**: Documents, data exports with download headers
5. **Error Pages**: Formatted error responses with context
6. **Partial Content**: HTML fragments for AJAX requests

## Best Practices

### Content Type Consistency
```python
# Ensure content matches content type
json_result = TemplateResult(
    content={"key": "value"},  # Dict for JSON
    content_type=ContentTypes.json,
    status_code=200,
    kwargs={}
)

html_result = TemplateResult(
    content="<h1>Title</h1>",  # String for HTML
    content_type=ContentTypes.html,
    status_code=200,
    kwargs={}
)
```

### Status Code Appropriateness
```python
# Use appropriate status codes
created_result = TemplateResult(
    content={"id": 123, "status": "created"},
    status_code=201,  # Created, not 200
    content_type=ContentTypes.json,
    kwargs={}
)

no_content_result = TemplateResult(
    content="",
    status_code=204,  # No Content
    content_type=ContentTypes.plain,
    kwargs={}
)
```

### Metadata Usage
```python
# Include useful metadata in kwargs
result = TemplateResult(
    content="<h1>User Profile</h1>",
    status_code=200,
    content_type=ContentTypes.html,
    kwargs={
        "user_id": 123,
        "render_time": 0.045,
        "template_name": "user_profile.html",
        "cache_key": "user_123_profile"
    }
)
```

### Method Chaining for Modifications
```python
# Use update() for clean modifications
final_result = base_result.update(
    status_code=200
).update(
    kwargs={"processed": True, "timestamp": "2024-01-01"}
)
```

## Performance Considerations

- TemplateResult is lightweight with minimal overhead
- Content should be pre-processed and ready for response
- Large content should be handled efficiently (streaming for files)
- Metadata in kwargs should be kept reasonable in size

## Thread Safety

- TemplateResult instances are not inherently thread-safe
- Each request should have its own TemplateResult instance
- The update() method modifies the instance in-place
- Avoid sharing instances between concurrent requests