# Location

The `Location` class represents browser location information including URL components, host details, and routing information.

## Location Class

### Constructor
```python
def __init__(
    self,
    host: str,
    url: str,
    origin: str,
    route: str,
    protocol: str
):
```

**Parameters:**
- `host`: Host portion of the URL (domain and port)
- `url`: Complete URL string
- `origin`: Origin of the URL (protocol + host)
- `route`: Route or path portion of the URL
- `protocol`: Protocol scheme (http, https, etc.)

### Properties

#### URL Components
- `host`: Host name and port (e.g., "example.com:8080")
- `url`: Full URL string
- `origin`: Origin (protocol + host, e.g., "https://example.com")
- `route`: Path/route portion (e.g., "/api/users")
- `protocol`: Protocol scheme (e.g., "https:")

## Usage Example

```python
from pyweber.models.window import Location

# Create location instance
location = Location(
    host="api.example.com:443",
    url="https://api.example.com:443/users/profile?id=123",
    origin="https://api.example.com:443",
    route="/users/profile",
    protocol="https:"
)

# Access location properties
print(location.host)      # api.example.com:443
print(location.url)       # https://api.example.com:443/users/profile?id=123
print(location.origin)    # https://api.example.com:443
print(location.route)     # /users/profile
print(location.protocol)  # https:
```

## URL Component Breakdown

### Host
- Contains domain name and optional port
- Examples: "localhost:8000", "example.com", "api.site.com:443"
- May include subdomains

### URL
- Complete URL including all components
- Examples: "https://example.com/path?query=value#fragment"
- Full address as seen in browser address bar

### Origin
- Combination of protocol and host
- Examples: "https://example.com", "http://localhost:3000"
- Used for CORS and security policies

### Route
- Path portion of the URL after the host
- Examples: "/", "/api/users", "/products/123"
- Does not include query parameters or fragments

### Protocol
- URL scheme with colon
- Examples: "https:", "http:", "ftp:", "ws:"
- Indicates how to access the resource

## Common Use Cases

1. **Navigation**: Tracking current page location
2. **Routing**: Determining which route handler to use
3. **Security**: Validating origins for CORS
4. **Analytics**: Tracking page visits and navigation
5. **Deep Linking**: Constructing URLs for specific content

## Integration

The Location class is used by:
- `Window` class for browser location information
- Routing systems for URL parsing
- Navigation components
- Security middleware for origin validation

## Browser Compatibility

Location information typically maps to JavaScript's `location` object:
- `location.host` → `host`
- `location.href` → `url`
- `location.origin` → `origin`
- `location.pathname` → `route`
- `location.protocol` → `protocol`

## Example Locations

### Simple Website
```python
simple_location = Location(
    host="example.com",
    url="https://example.com/about",
    origin="https://example.com",
    route="/about",
    protocol="https:"
)
```

### API Endpoint
```python
api_location = Location(
    host="api.service.com:443",
    url="https://api.service.com:443/v1/users",
    origin="https://api.service.com:443",
    route="/v1/users",
    protocol="https:"
)
```

### Local Development
```python
local_location = Location(
    host="localhost:8080",
    url="http://localhost:8080/dashboard",
    origin="http://localhost:8080",
    route="/dashboard",
    protocol="http:"
)
```

### Root Path
```python
root_location = Location(
    host="mysite.com",
    url="https://mysite.com/",
    origin="https://mysite.com",
    route="/",
    protocol="https:"
)
```

## URL Parsing Notes

- Query parameters and fragments are not stored separately
- The `url` property contains the complete URL
- The `route` property focuses on the path for routing logic
- Port numbers are included in `host` when non-standard
- Protocol always includes the trailing colon