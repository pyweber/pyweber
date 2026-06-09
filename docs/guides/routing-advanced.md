# Routing: path params, query params and groups

## Path parameters

```python
@app.route('/users/{user_id}')
def user_page(user_id: int):
    return pw.Element('h1', content=f'User {user_id}')
```

Type annotations are used for validation and OpenAPI generation.

## Query parameters (1.2.0+)

Define expected query keys in the route pattern:

```python
@app.route('/login?session={session}')
def login(session: str):
    return pw.Element('p', content=f'Session token: {session}')
```

When a user visits `/login?session=abc123`, `session` is injected into the handler — same as path params.

Query placeholders are **not** mixed with path placeholders in Swagger as body fields (fixed in 1.2.0).

## Multiple HTTP methods on one path

Pyweber allows **one route registration per URL path**. All supported verbs go in a single `methods` list:

```python
@app.route('/resource', methods=['GET', 'POST', 'DELETE'])
def resource(request: pw.Request, **kw):
    if request.method == 'GET':
        return list_items()
    if request.method == 'POST':
        return create_item(**kw)
    if request.method == 'DELETE':
        return delete_item(**kw)
```

### Adding methods later

```python
app.add_route('/resource', template=resource, methods=['GET', 'POST'])
app.update_route('/resource', methods=['GET', 'POST', 'DELETE'])
```

### What does *not* work

Registering the same path twice raises **`RouteAlreadyExistError`**:

```python
# Wrong — second add_route fails
app.add_route('/resource', template=handle_get, methods=['GET'])
app.add_route('/resource', template=handle_delete, methods=['DELETE'])  # raises
```

Use one handler (or one template class) that branches on `request.method`, or a single `@app.route` with all methods.

### 405 Method Not Allowed (1.3.0+)

If the path exists but the HTTP verb is not in `route.methods`, Pyweber returns **405** (not 404) and sets the `Allow` header:

```http
HTTP/1.1 405 Method Not Allowed
Allow: GET, POST
```

Example: route allows `GET, POST` but client sends `DELETE` → 405 with `Allow: GET, POST`.

## Route decorator options

```python
@app.route(
    '/api/items',
    methods=['GET', 'POST'],
    name='items_api',
    group='api',
    content_type=pw.ContentTypes.json,
    title='Items API',
    middlewares=[auth_middleware],
)
def items():
    return {'items': []}
```

## Redirects

```python
app.add_route('/new-home', template=HomePage(), name='home')
app.redirect('/old-home', 'home', status_code=301)
```

!!! warning "Redirect loops"
    Circular redirects are detected per request. A loop surfaces as a server error page — fix the redirect chain in your routes.

## OpenAPI / Swagger

Interactive docs are available at **`/docs`** when the app is running. Schemas are generated from route signatures and type hints.

## Next steps

- [Route class reference](../routing/route.md) — full API
- [Reactivity](reactivity.md#template-handoff-http--websocket) — Template Handoff on page load
- [Pyweber application](../core/pyweber.md) — middleware and static files
