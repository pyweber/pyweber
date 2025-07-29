# Response

The `Response` class handles HTTP response generation and formatting for both WSGI and ASGI modes, providing a unified interface for creating HTTP responses with proper headers, status codes, and content.

## Response Class

### Constructor
```python
def __init__(
    self,
    request: Request,
    response_content: bytes,
    code: int,
    cookies: list[str],
    response_type: ContentTypes,
    route: str
):
```

**Parameters:**
- `request`: The original Request object
- `response_content`: Response body content in bytes
- `code`: HTTP status code (e.g., 200, 404, 500)
- `cookies`: List of cookies to set in the response
- `response_type`: Content type from ContentTypes enum
- `route`: The route that generated this response

### Properties

#### Basic Response Information
- `headers`: Dictionary containing all response headers
- `request`: The original Request object that generated this response
- `http_version`: HTTP version from the original request
- `response_date`: Response generation date in GMT format
- `response_type`: Content type of the response
- `response_content`: Response body content in bytes

#### Status and Routing
- `code`: HTTP status code as integer
- `status_code`: Formatted status code string with additional headers for specific codes
- `request_path`: Original request path
- `response_path`: Route path that handled the request

#### Cookies
- `cookies`: List of cookies to be set in the response

### Methods

#### `set_header(key: str, value: str)`
Adds a new header to the response.

**Parameters:**
- `key`: Header name
- `value`: Header value

#### `update_header(key: str, value: str | bytes | int | float)`
Updates an existing header value if the header exists in the response.

**Parameters:**
- `key`: Header name
- `value`: New header value

#### `new_content(value: bytes)`
Updates the response content and automatically adjusts the Content-Length header.

**Parameters:**
- `value`: New response content in bytes

#### `build_response` (Property)
Builds the complete HTTP response as bytes, including:
- Status line
- All headers
- Response body
- Console logging with colored output

### Special Behavior

#### Status Code Handling
The `status_code` property provides enhanced status codes with additional headers:

- **3xx (Redirects)**: Adds `Location` header
- **401 (Unauthorized)**: Adds `WWW-Authenticate` header with app name
- **405 (Method Not Allowed)**: Adds `Allow` header with supported methods
- **503 (Service Unavailable)**: Adds `Retry-After` header

#### Default Headers
The response automatically includes these headers:
- `Content-Type`: Set from response_type parameter with UTF-8 charset
- `Content-Length`: Automatically calculated from response content
- `Connection`: Set to 'Close'
- `Method`: HTTP method from original request
- `Http-Version`: HTTP version from original request
- `Status`: HTTP status code
- `Server`: Set to 'Pyweber/1.0'
- `Date`: Current UTC timestamp in HTTP format
- `Set-Cookie`: List of cookies to set
- `Request-Path`: Original request path
- `Response-Path`: Route that handled the request

### Dictionary-like Access

The Response class supports dictionary-like access through `__getitem__`:

```python
# Get all data
response_data = response[None]  # Returns {'headers': headers, 'body': body}

# Get headers only
headers = response['headers']

# Get body only
body = response['body']
```

## Usage Example

```python
from pyweber.utils.types import ContentTypes
from pyweber.models.request import Request
from pyweber.models.response import Response

# Create a successful JSON response
request = Request(headers=wsgi_headers, body=request_body)
json_content = b'{"message": "Success", "data": []}'
cookies = ["session_id=abc123; Path=/; HttpOnly"]

response = Response(
    request=request,
    response_content=json_content,
    code=200,
    cookies=cookies,
    response_type=ContentTypes.json,
    route="/api/data"
)

# Add custom header
response.set_header("X-Custom-Header", "custom-value")

# Update existing header
response.update_header("Server", "Pyweber/2.0")

# Get the complete HTTP response
http_response = response.build_response
```

## Console Output

The `build_response` property automatically logs the request and response to the console with color-coded status:
- **Green**: 2xx status codes (success)
- **Yellow**: 3xx status codes (redirects)
- **Red**: 4xx and 5xx status codes (errors)
- **Blue**: 1xx status codes (informational)

## Integration

The Response class integrates with:
- `Request` objects for request context
- `ContentTypes` enum for content type management
- `HTTPStatusCode` utility for status code formatting
- `PrintLine` utility for colored console output
- Application configuration for authentication realm names