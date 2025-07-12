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
- **Raw JSON**: `http://localhost:8800/_pyweber/{uuid}/openapi.json`

> UUID is used to avoid caching issues.

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
- Explore [Templates](template.md) for creating UI components
- Learn about [Elements](element.md) for DOM manipulation
- Understand [Events](events.md) for handling user interactions
- Set up routing with the [PyWeber class](router.md)

