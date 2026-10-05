# OpenAPI/Swagger Integration Documentation

## Overview

PyWeber provides **zero-configuration** OpenAPI 3.0 documentation with automatic Swagger UI generation. By simply adding type hints to your route functions, the framework generates full-featured, interactive API documentation.

## Key Features

### Zero Configuration

- **No setup needed** — documentation is generated automatically
- **Auto-discovery** of all route parameters and data models
- **Instant Swagger UI** at `/docs` endpoint

### Flexible Type Support

- **Pydantic** models for advanced validation
- **Dataclasses** for clean data handling
- **Vanilla Python classes** (with `__init__` or annotations)
- **Primitive types**: `int`, `str`, `float`, `bool`, etc.

### Smart Documentation

- Auto-generated examples and formats
- Real-time schema reflection on code changes
- Integrated Swagger UI for "Try it out" functionality

## Quick Start

```python
import pyweber as pw
from pydantic import BaseModel

app = pw.Pyweber()

class User(BaseModel):
    username: str
    email: str
    age: int = 25

@app.route('/users/{user_id}', methods=['POST'])
def create_user(user_id: int, name: str, user: User):
    return pw.Element(tag='p', content=f'User {user_id} created successfully')

if __name__ == '__main__':
    pw.run()
```

> Access Swagger UI at `http://localhost:8800/docs`

## Supported Model Types

### 1. Pydantic Models

```python
class Profile(BaseModel):
    username: str
    email: EmailStr
    age: Optional[int] = None
```

- Built-in validation
- Optional/required field detection
- Rich type support (UUID, EmailStr, etc.)

### 2. Dataclasses

```python
@dataclass
class Product:
    name: str
    price: float
    in_stock: bool = True
```

- Lightweight and readable
- Type-safe with default value support

### 3. Vanilla Classes

```python
class Settings:
    theme: str
    language: str = 'en'
```

- No external dependencies
- Supports both `__init__` and annotation-based definitions

## Advanced Features

### Mixed Parameters Example

```python
@app.route('/users/{user_id}/permissions', methods=['POST'])
def set_permissions(
    user_id: int,
    force: bool,
    notify: str = "email",
    user_data: UserData
):
    return {"status": "ok"}
```

Request body schema merges primitives and object models seamlessly.

### Example & Format Detection

```python
class Event(BaseModel):
    id: UUID
    name: str
    start_date: datetime
```

Auto-generates:

```json
{
  "id": {"type": "string", "format": "uuid"},
  "start_date": {"type": "string", "format": "date-time"}
}
```

## Accessing Documentation

- **Swagger UI**: `http://localhost:8800/docs`
- **Raw JSON**: `http://localhost:8800/openapi.json` (or `OpenAPIConfig.openapi_url`)
- **Cache-busting alias**: `http://localhost:8800/_pyweber/{uuid}/openapi.json`

## Organising the Swagger page

!!! tip "Added in 1.8.3"

### Groups (tags)

Routes without `tags=` are grouped by their **first path segment**, so `/admin/estrutura/departamentos` lands under **admin** and `/entrar/senha` under **entrar** — no more single *default* list. Explicit tags or route groups always win:

```python
@app.route('/users', tags=['Utilizadores'])
def users(): ...
```

Add descriptions (and an order) for groups with `OpenAPIConfig(tags=[...])`, or turn automatic grouping off with `auto_tags=False`:

```python
app = pw.Pyweber(openapi=pw.OpenAPIConfig(
    tags=[
        {'name': 'admin', 'description': 'Back-office da organização'},
        {'name': 'entrar', 'description': 'Login, SSO e recuperação de senha'},
    ],
))
```

### Summaries and descriptions

Each operation's summary is `title=` → first line of the docstring → the function name made readable (`listar_departamentos` → *Listar departamentos*). The full docstring becomes the description.

```python
@app.route('/admin/estrutura/departamentos')
def listar_departamentos():
    """Lista os departamentos.

    Devolve apenas departamentos ativos da organização atual.
    """
```

### Authentication

**Login cookie (`pyweber.auth`).** Routes decorated with `@login_required` (or `role_required` / `permission_required`) show a lock and a *Requires login* note listing the required roles/permissions. The signed `pyweber_user` cookie is documented as the `PyweberSession` scheme. Sign in through your app in the same browser and **Try it out** sends the cookie automatically. Put `@app.route` *above* `@login_required` so the docs can see it. Rename the scheme with `session_auth_scheme='Sessao'` or disable it with `session_auth_scheme=None`.

**Tokens and API keys.** Declare schemes once and Swagger shows the **Authorize** button; credentials persist across page reloads:

```python
app = pw.Pyweber(openapi=pw.OpenAPIConfig(
    security_schemes={
        'BearerAuth': pw.HTTPBearer(verify=verify_token),
        'ApiKeyAuth': pw.APIKeyHeader(name='X-API-Key', verify=check_key),
    },
    security=['BearerAuth'],        # global default; security=[] on a route makes it public
))
```

A route that uses both a scheme and `@login_required` is documented as accepting **either**.

**CSRF.** "Try it out" requests automatically send the `X-CSRF-Token` header from the `pyweber_csrf` cookie, so POST/PUT/DELETE calls from `/docs` are not rejected with 403.

### Swagger UI options

Defaults: deep links, persistent authorization, tag filter, request duration, operations listed (collapsed), alphabetical sorting, "Try it out" off until clicked. Override any [Swagger UI option](https://swagger.io/docs/open-source-tools/swagger-ui/usage/configuration/):

```python
pw.OpenAPIConfig(swagger_ui_parameters={'docExpansion': 'none', 'tryItOutEnabled': True})
```

The `/docs` page also honours a custom `openapi_url` and uses `OpenAPIConfig.title` as page title.

## Best Practices

### Use explicit type hints

```python
def create_user(name: str, user: User): ...
```

### Provide default values

```python
class Preferences(BaseModel):
    theme: str = 'light'
    notifications: bool = True
```

### Use descriptive routes

```python
@app.route('/users/{id}', name='get_user', methods=['GET'])
```

### Avoid dynamic args

```python
def bad_route(*args, **kwargs): ...  # not supported
```

## Error Handling

Unsupported patterns (e.g., `**kwargs`) will raise meaningful errors during startup.

## Performance

- **Lazy Evaluation**: schema only built on demand
- **Caching**: route-wise schema caching
- **Efficient Introspection**: no unnecessary overhead
- **No Extra Dependencies**: pure Python solution

## Migration Guide

### From FastAPI

```python
# FastAPI
@app.post("/users")
def create(user: User): ...

# PyWeber
@app.route("/users", methods=["POST"])
def create(user: User): ...
```

### From Flask

```python
# Flask
@app.route('/users', methods=['POST'])
def create():
    user = User(**request.get_json())

# PyWeber
@app.route('/users', methods=['POST'])
def create(user: User): ...  # auto-instantiated
```

## Conclusion

PyWeber redefines how API documentation should work:

- Instant OpenAPI without boilerplate
- Full type introspection across all class types
- Developer-focused with built-in smart defaults

Now, you can explore more about pyweber:

- [Element model guide](guides/element-model.md)
- [Templates](ui/template.md) for creating UI components
- [Elements](ui/element.md) for DOM manipulation
- [Events](interaction/events.md) for handling user interactions
- [Pyweber application](core/pyweber.md) for routing