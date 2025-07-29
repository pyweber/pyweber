# ContentResult Class Documentation

The `ContentResult` class is a dataclass that represents the final content result ready for HTTP response, containing processed content, status code, content type, and response headers.

## Dependencies

```python
from dataclasses import dataclass
from typing import Any
from pyweber.utils.types import ContentTypes
```

## ContentResult Class

### Dataclass Definition
```python
@dataclass
class ContentResult:
```

The ContentResult class is implemented as a dataclass for automatic initialization and representation methods.

### Fields

#### `content: Any`
The final processed content ready for HTTP response.
- Can be string, bytes, dict, or other serializable content
- Represents the actual response body to be sent to the client

#### `status_code: int`
HTTP status code for the response.
- Standard HTTP status codes (200, 404, 500, etc.)
- Determines the HTTP response status line

#### `content_type: ContentTypes`
Content type for the response.
- Must be a ContentTypes enum value
- Used to set the Content-Type HTTP header

#### `headers: dict[str, str]`
Additional HTTP headers for the response.
- Dictionary of header name-value pairs
- Merged with default headers during response generation

### Methods

#### `update(**kwargs) -> ContentResult`
Updates the ContentResult fields and returns self for method chaining.

**Parameters:**
- `content`: New content (optional)
- `status_code`: New status code (optional)
- `content_type`: New content type (optional)
- `headers`: New headers dictionary (optional)

**Returns:** Self (ContentResult instance) for method chaining

**Behavior:**
- Only updates fields that are provided (not None)
- Preserves existing values for unprovided fields
- Returns self to enable method chaining

## Usage Examples

### Basic ContentResult Creation
```python
from pyweber.models.routes import ContentResult
from pyweber.utils.types import ContentTypes

# Create HTML content result
html_result = ContentResult(
    content="<!DOCTYPE html><html><body><h1>Hello World</h1></body></html>",
    status_code=200,
    content_type=ContentTypes.html,
    headers={"Cache-Control": "no-cache"}
)

print(html_result.content)      # Full HTML content
print(html_result.status_code)  # 200
print(html_result.content_type) # ContentTypes.html
print(html_result.headers)      # {"Cache-Control": "no-cache"}
```

### JSON API Response
```python
import json

# Create JSON content result
api_data = {"users": [{"id": 1, "name": "John"}], "total": 1}
json_result = ContentResult(
    content=json.dumps(api_data),
    status_code=200,
    content_type=ContentTypes.json,
    headers={
        "Access-Control-Allow-Origin": "*",
        "X-API-Version": "1.0"
    }
)
```

### File Download Response
```python
# Create file download result
file_content = "Name,Email\nJohn,john@example.com\nJane,jane@example.com"
download_result = ContentResult(
    content=file_content,
    status_code=200,
    content_type=ContentTypes.csv,
    headers={
        "Content-Disposition": "attachment; filename=users.csv",
        "Content-Length": str(len(file_content))
    }
)
```

### Binary Content Response
```python
# Create image response
with open("image.png", "rb") as f:
    image_data = f.read()

image_result = ContentResult(
    content=image_data,
    status_code=200,
    content_type=ContentTypes.png,
    headers={
        "Cache-Control": "public, max-age=3600",
        "Content-Length": str(len(image_data))
    }
)
```

### Error Response
```python
# Create error content result
error_result = ContentResult(
    content="<html><body><h1>404 - Page Not Found</h1></body></html>",
    status_code=404,
    content_type=ContentTypes.html,
    headers={"X-Error-Type": "not_found"}
)
```

### Redirect Response
```python
# Create redirect result
redirect_result = ContentResult(
    content="",  # Empty content for redirects
    status_code=302,
    content_type=ContentTypes.html,
    headers={"Location": "/new-location"}
)
```

### Updating ContentResult
```python
# Update specific fields
updated_result = html_result.update(
    status_code=201,
    headers={"X-Custom-Header": "value"}
)

print(updated_result.status_code)  # 201
print(updated_result.headers)      # {"X-Custom-Header": "value"}

# Method chaining
final_result = html_result.update(
    content="<h1>Updated Content</h1>"
).update(
    headers={"Last-Modified": "Wed, 21 Oct 2015 07:28:00 GMT"}
)
```

## Integration with PyWeber

### Response Generation Pipeline
```python
# ContentResult is the final step before HTTP response
async def generate_response(self, template_result: TemplateResult):
    # Process content based on type
    if template_result.content_type == ContentTypes.json:
        content = json.dumps(template_result.content)
    elif isinstance(template_result.content, bytes):
        content = template_result.content
    else:
        content = str(template_result.content)

    # Generate headers
    headers = self._generate_default_headers(template_result)

    # Create final content result
    return ContentResult(
        content=content,
        status_code=template_result.status_code,
        content_type=template_result.content_type,
        headers=headers
    )
```

### HTTP Response Creation
```python
# Convert ContentResult to actual HTTP response
def create_http_response(content_result: ContentResult):
    response = HTTPResponse()
    response.status_code = content_result.status_code

    # Set content type header
    response.headers["Content-Type"] = content_result.content_type.value

    # Add custom headers
    for name, value in content_result.headers.items():
        response.headers[name] = value

    # Set response body
    if isinstance(content_result.content, bytes):
        response.body = content_result.content
    else:
        response.body = str(content_result.content).encode('utf-8')

    return response
```

### Middleware Post-Processing
```python
# Middleware can modify ContentResult before response
def security_headers_middleware(content_result: ContentResult):
    security_headers = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block"
    }

    return content_result.update(
        headers={**content_result.headers, **security_headers}
    )

def compression_middleware(content_result: ContentResult):
    if content_result.content_type in [ContentTypes.html, ContentTypes.css, ContentTypes.javascript]:
        # Compress content
        compressed_content = gzip.compress(content_result.content.encode())
        return content_result.update(
            content=compressed_content,
            headers={
                **content_result.headers,
                "Content-Encoding": "gzip",
                "Content-Length": str(len(compressed_content))
            }
        )
    return content_result
```

## Content Type Handling

### Text Content
```python
# HTML content
html_content = ContentResult(
    content="<!DOCTYPE html><html><head><title>Page</title></head><body><h1>Content</h1></body></html>",
    status_code=200,
    content_type=ContentTypes.html,
    headers={"Charset": "utf-8"}
)

# Plain text content
text_content = ContentResult(
    content="This is plain text content",
    status_code=200,
    content_type=ContentTypes.plain,
    headers={"Charset": "utf-8"}
)

# CSS content
css_content = ContentResult(
    content="body { margin: 0; padding: 20px; }",
    status_code=200,
    content_type=ContentTypes.css,
    headers={"Cache-Control": "public, max-age=86400"}
)
```

### JSON Content
```python
# API response
api_response = ContentResult(
    content='{"status": "success", "data": {"id": 123}}',
    status_code=200,
    content_type=ContentTypes.json,
    headers={
        "Access-Control-Allow-Origin": "*",
        "X-API-Version": "1.0"
    }
)

# Error response
error_response = ContentResult(
    content='{"status": "error", "message": "Invalid request"}',
    status_code=400,
    content_type=ContentTypes.json,
    headers={"X-Error-Code": "INVALID_REQUEST"}
)
```

### Binary Content
```python
# Image response
image_response = ContentResult(
    content=image_bytes,
    status_code=200,
    content_type=ContentTypes.jpeg,
    headers={
        "Cache-Control": "public, max-age=3600",
        "Content-Length": str(len(image_bytes))
    }
)

# PDF response
pdf_response = ContentResult(
    content=pdf_bytes,
    status_code=200,
    content_type=ContentTypes.pdf,
    headers={
        "Content-Disposition": "inline; filename=document.pdf",
        "Content-Length": str(len(pdf_bytes))
    }
)
```

## HTTP Headers Management

### Common Headers
```python
# Caching headers
cached_result = ContentResult(
    content="<h1>Cached Content</h1>",
    status_code=200,
    content_type=ContentTypes.html,
    headers={
        "Cache-Control": "public, max-age=3600",
        "ETag": '"abc123"',
        "Last-Modified": "Wed, 21 Oct 2015 07:28:00 GMT"
    }
)

# Security headers
secure_result = ContentResult(
    content="<h1>Secure Content</h1>",
    status_code=200,
    content_type=ContentTypes.html,
    headers={
        "Strict-Transport-Security": "max-age=31536000",
        "Content-Security-Policy": "default-src 'self'",
        "X-Frame-Options": "DENY"
    }
)
```

### CORS Headers
```python
# CORS-enabled API response
cors_result = ContentResult(
    content='{"message": "API response"}',
    status_code=200,
    content_type=ContentTypes.json,
    headers={
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE",
        "Access-Control-Allow-Headers": "Content-Type, Authorization"
    }
)
```

### Custom Headers
```python
# Application-specific headers
custom_result = ContentResult(
    content="<h1>Custom Response</h1>",
    status_code=200,
    content_type=ContentTypes.html,
    headers={
        "X-App-Version": "1.2.3",
        "X-Request-ID": "req-123456",
        "X-Processing-Time": "0.045s"
    }
)
```

## Status Code Handling

### Success Responses
```python
# OK response
ok_result = ContentResult(
    content="<h1>Success</h1>",
    status_code=200,
    content_type=ContentTypes.html,
    headers={}
)

# Created response
created_result = ContentResult(
    content='{"id": 123, "status": "created"}',
    status_code=201,
    content_type=ContentTypes.json,
    headers={"Location": "/users/123"}
)

# No content response
no_content_result = ContentResult(
    content="",
    status_code=204,
    content_type=ContentTypes.plain,
    headers={}
)
```

### Error Responses
```python
# Bad request
bad_request_result = ContentResult(
    content='{"error": "Invalid input"}',
    status_code=400,
    content_type=ContentTypes.json,
    headers={"X-Error-Type": "validation"}
)

# Not found
not_found_result = ContentResult(
    content="<h1>404 - Page Not Found</h1>",
    status_code=404,
    content_type=ContentTypes.html,
    headers={}
)

# Server error
server_error_result = ContentResult(
    content="<h1>500 - Internal Server Error</h1>",
    status_code=500,
    content_type=ContentTypes.html,
    headers={"X-Error-ID": "err-789"}
)
```

## Common Use Cases

1. **Web Pages**: HTML content with appropriate headers
2. **API Responses**: JSON data with CORS and versioning headers
3. **File Downloads**: Binary content with download headers
4. **Static Assets**: CSS, JS, images with caching headers
5. **Error Pages**: Error content with diagnostic headers
6. **Redirects**: Empty content with Location header

## Best Practices

### Header Management
```python
# Use appropriate headers for content type
html_result = ContentResult(
    content="<h1>Page</h1>",
    status_code=200,
    content_type=ContentTypes.html,
    headers={
        "Cache-Control": "no-cache",  # For dynamic content
        "X-Content-Type-Options": "nosniff"  # Security
    }
)

json_result = ContentResult(
    content='{"data": "value"}',
    status_code=200,
    content_type=ContentTypes.json,
    headers={
        "Access-Control-Allow-Origin": "*",  # For APIs
        "X-API-Version": "1.0"  # Versioning
    }
)
```

### Content Length
```python
# Set Content-Length for binary content
binary_result = ContentResult(
    content=binary_data,
    status_code=200,
    content_type=ContentTypes.pdf,
    headers={"Content-Length": str(len(binary_data))}
)
```

### Method Chaining
```python
# Use update() for clean modifications
final_result = base_result.update(
    status_code=200
).update(
    headers={"X-Processed": "true"}
)
```

### Error Handling
```python
def create_error_result(status_code: int, message: str):
    return ContentResult(
        content=f"<h1>Error {status_code}</h1><p>{message}</p>",
        status_code=status_code,
        content_type=ContentTypes.html,
        headers={"X-Error": "true"}
    )
```

## Performance Considerations

- ContentResult should contain final, ready-to-send content
- Large content should be handled efficiently (consider streaming)
- Headers dictionary should be kept reasonable in size
- Binary content should be handled as bytes, not strings

## Thread Safety

- ContentResult instances are not inherently thread-safe
- Each request should have its own ContentResult instance
- The update() method modifies the instance in-place
- Avoid sharing instances between concurrent requests