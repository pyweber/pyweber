# Request

The `Request` class is responsible for processing and parsing HTTP requests in both WSGI and ASGI modes, providing a unified interface for accessing request data.

## Enums

### RequestMode
Enum that defines the request operation modes:
- `asgi`: ASGI mode (Asynchronous Server Gateway Interface)
- `wsgi`: WSGI mode (Web Server Gateway Interface)

## Data Classes

### ClientInfo
Dataclass that stores client information:
- `host` (str): Client host address
- `port` (int): Client connection port

## Request Class

### Constructor
```python
def __init__(
    self,
    headers: Union[str, dict[str, Union[tuple[str, str], str]]],
    body: Union[bytes] = None,
    client_info: ClientInfo = None
):
```

**Parameters:**
- `headers`: Request headers (string for WSGI or dict for ASGI)
- `body`: Request body in bytes (optional)
- `client_info`: Client information (optional)

### Properties

#### Basic Information
- `request_mode`: Request mode (WSGI or ASGI)
- `client_info`: Client information
- `raw_headers`: Raw request headers
- `raw_body`: Raw request body
- `first_line`: First line of the HTTP request

#### HTTP Headers
- `host`: Request host
- `port`: Port extracted from host header
- `content_length`: Content length
- `content_type`: Content type
- `user_agent`: Client user agent
- `origin`: Request origin
- `referrer`: Request referrer
- `headers`: Dictionary with all headers

#### Content Negotiation
- `accept`: List of accepted content types
- `accept_encoding`: List of accepted encodings
- `accept_language`: List of accepted languages

#### Request Data
- `cookies`: Dictionary with request cookies
- `body`: Parsed request body (JSON, form-encoded, or form-data)
- `method`: HTTP method (GET, POST, etc.)
- `scheme`: Request scheme (HTTP/HTTPS)
- `path`: URL path
- `query_params`: Query string parameters

### Configuration Properties

#### `request_parts_splitter`
Returns `'\r\n\r\n'` - separator between headers and body.

## Supported Content Types

The `body` property automatically parses different content types:

1. **JSON** (`application/json`): Returns parsed Python object
2. **Form URL-encoded** (`application/x-www-form-urlencoded`): Returns dictionary
3. **Form Data** (`multipart/form-data`): Returns dictionary with files and fields
4. **Others**: Returns empty dictionary

## Usage Example

```python
# WSGI Request
wsgi_headers = "GET /api/users HTTP/1.1\r\nHost: example.com\r\nContent-Type: application/json"
request = Request(headers=wsgi_headers, body=b'{"name": "John"}')

print(request.method)  # GET
print(request.path)    # /api/users
print(request.host)    # example.com
print(request.body)    # {'name': 'John'}

# ASGI Request
asgi_headers = {
    'method': 'POST',
    'scheme': 'https',
    'path': '/upload',
    'headers': [(b'content-type', b'multipart/form-data')]
}
request = Request(headers=asgi_headers, body=form_data_bytes)
```

## Error Handling

- `TypeError`: Raised when headers type is not valid
- `TypeError`: Raised when request_mode is not a RequestMode instance
- `TypeError`: Raised when client_info is not a ClientInfo instance

## Representation

The class implements `__repr__()` returning:
```
Request(method=GET, mode=RequestMode.wsgi)
```