# Headers

The `Headers` class provides a convenient way to construct and format HTTP request headers with proper validation and formatting for both text and JSON representations.

## Headers Class

### Constructor
```python
def __init__(
    self,
    url: str,
    method: str = 'GET',
    content_type: ContentTypes = ContentTypes.html,
    content_length: int = None,
    cookie: dict[str, str] = None,
    user_agent: str = None,
    http_version: str = 1.1,
    **headers: str
):
```

**Parameters:**
- `url`: Target URL (required)
- `method`: HTTP method (default: 'GET')
- `content_type`: Content type from ContentTypes enum (default: ContentTypes.html)
- `content_length`: Content length in bytes (optional)
- `cookie`: Dictionary of cookies (optional)
- `user_agent`: User agent string (optional)
- `http_version`: HTTP version (1.0, 1.1, or 2.0, default: 1.1)
- `**headers`: Additional custom headers

### Properties (Read-Only)

#### Basic Properties
- `url`: Complete URL
- `method`: HTTP method (uppercase)
- `content_type`: Content type value
- `content_length`: Content length in bytes
- `cookie`: Formatted cookie string
- `user_agent`: User agent string
- `http_version`: Formatted HTTP version (e.g., "HTTP/1.1")

#### Parsed URL Components
- `host`: Host portion of the URL (including protocol and port)
- `path`: Path portion of the URL (defaults to "/" if not specified)

### Property Setters with Validation

#### `http_version` Setter
Validates and formats HTTP version.
- **Accepted values:** 1.0, 1.1, 2.0
- **Format:** Converts to "HTTP/X.X" format
- **Raises:** `ValueError` for invalid versions

#### `cookie` Setter
Validates and formats cookie dictionary.
- **Input:** Dictionary of key-value pairs
- **Output:** Formatted as "key1=value1&key2=value2"
- **Raises:** `TypeError` if not a dictionary

#### `content_type` Setter
Validates ContentTypes enum value.
- **Default:** ContentTypes.html if None provided
- **Raises:** `TypeError` if not a ContentTypes instance

#### `user_agent` Setter
Validates user agent string.
- **Raises:** `TypeError` if not a string

#### `content_length` Setter
Validates content length integer.
- **Default:** 0 if None provided
- **Raises:** `TypeError` if not an integer

#### `method` Setter
Validates and formats HTTP method.
- **Default:** "GET" if None provided
- **Format:** Converts to uppercase

#### `url` Setter
Validates URL format using regex pattern.
- **Supported protocols:** http://, https://, www., ftp://
- **Supported hosts:** Domain names, IPv4 addresses, localhost
- **Optional port:** Extracted if present
- **Raises:** `ValueError` for invalid URLs or empty values

### Output Methods

#### `text` Property
Returns formatted HTTP request headers as text string.

**Format:**
```
METHOD /path HTTP/version
Host:              hostname
Header-Name:       header-value
...
```

#### `json` Property
Returns headers formatted for ASGI/JSON representation.

**Returns:** Dictionary with 'headers' key containing list of (name, value) byte tuples.

## Usage Examples

### Basic Usage
```python
from pyweber.models.headers import Headers
from pyweber.utils.types import ContentTypes

# Create basic headers
headers = Headers(
    url="https://api.example.com/users",
    method="POST",
    content_type=ContentTypes.json,
    content_length=156
)

# Get text representation
print(headers.text)
# POST /users HTTP/1.1
# Host:              https://api.example.com
# Content-type:      application/json
# Content-length:    156
```

### Advanced Usage with Cookies and Custom Headers
```python
# Create headers with cookies and custom headers
headers = Headers(
    url="https://example.com/api/data",
    method="GET",
    cookie={"session_id": "abc123", "theme": "dark"},
    user_agent="MyApp/1.0",
    http_version=2.0,
    authorization="Bearer token123",
    x_custom_header="custom-value"
)

# Access properties
print(headers.host)           # https://example.com
print(headers.path)           # /api/data
print(headers.cookie)         # session_id=abc123&theme=dark
print(headers.http_version)   # HTTP/2.0

# Get JSON representation for ASGI
json_headers = headers.json
print(json_headers['headers'])  # List of (name, value) byte tuples
```

### URL Validation Examples
```python
# Valid URLs
valid_urls = [
    "https://example.com",
    "http://localhost:8080/path",
    "https://192.168.1.1:3000/api",
    "ftp://files.example.com/downloads"
]

# Invalid URLs (will raise ValueError)
invalid_urls = [
    "not-a-url",
    "http://",
    "",
    "example.com"  # Missing protocol
]
```

## Error Handling

### URL Validation Errors
- `ValueError`: Raised for invalid URL format or empty URL
- Regex pattern validates protocol, domain/IP, optional port, and path

### Type Validation Errors
- `TypeError`: Raised for incorrect parameter types
- Each setter validates the expected data type

### HTTP Version Errors
- `ValueError`: Raised for unsupported HTTP versions
- Only 1.0, 1.1, and 2.0 are supported

## Integration

The Headers class integrates with:
- `ContentTypes` enum for content type management
- HTTP client libraries for request construction
- ASGI/WSGI frameworks for header formatting
- Request/Response classes for HTTP communication

## Common Use Cases

1. **HTTP Client Requests**: Building properly formatted request headers
2. **API Communication**: Setting content types, authentication, and custom headers
3. **Web Scraping**: Creating realistic browser-like headers
4. **Testing**: Generating test HTTP requests with various header combinations
5. **Proxy/Gateway**: Reformatting headers between different protocols