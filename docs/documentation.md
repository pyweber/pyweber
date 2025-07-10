# OpenAPI/Swagger Integration Documentation

## Overview

Pyweber provides **zero-configuration** OpenAPI 3.0 documentation with automatic Swagger UI generation. Simply add type hints to your route functions, and the framework automatically generates comprehensive API documentation with interactive testing capabilities.

## Key Features

### 🚀 Zero Configuration
- **No setup required** - just add type hints to your functions
- **Automatic detection** of all route parameters and types
- **Instant documentation** available at `/docs` endpoint

### 🔧 Universal Type Support
- **Pydantic Models** - Full validation and schema generation
- **Dataclasses** - Clean, structured data handling
- **Vanilla Classes** - Simple Python classes with annotations
- **Primitive Types** - int, str, float, bool with format support

### 📚 Intelligent Documentation
- **Automatic examples** generation for all supported types
- **Interactive testing** with "Try it out" functionality
- **Real-time schema** updates based on your code changes

## Quick Start

### Basic Example

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

**Result**: Automatic OpenAPI documentation with:
- Path parameter: `user_id` (integer)
- Request body with mixed fields: `name` (string) + User model properties
- Interactive Swagger UI at `http://localhost:8800/docs`

## Supported Model Types

### 1. Pydantic Models (Recommended)

```python
from pydantic import BaseModel, EmailStr
from typing import Optional

class UserProfile(BaseModel):
    username: str
    email: EmailStr
    age: Optional[int] = None
    is_active: bool = True

@app.route('/profile', methods=['POST'])
def update_profile(profile: UserProfile):
    return {"status": "updated"}
```

**Benefits:**
- ✅ Built-in validation
- ✅ Rich type support (EmailStr, UUID, etc.)
- ✅ Automatic OpenAPI schema generation
- ✅ Default values and optional fields

### 2. Dataclasses

```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class Product:
    name: str
    price: float
    category: str
    in_stock: bool = True
    description: Optional[str] = None

@app.route('/products', methods=['POST'])
def create_product(product: Product):
    return {"product_id": 123}
```

**Benefits:**
- ✅ Clean, readable code
- ✅ Automatic field detection
- ✅ Default value support
- ✅ Type safety

### 3. Vanilla Python Classes

```python
class Settings:
    theme: str
    language: str = 'en'
    notifications: bool = True

@app.route('/settings', methods=['PUT'])
def update_settings(user_id: int, settings: Settings):
    return {"message": "Settings updated"}
```

**Benefits:**
- ✅ Maximum simplicity
- ✅ No external dependencies
- ✅ Flexible structure
- ✅ Automatic instantiation

## Advanced Features

### Mixed Parameter Types

```python
from enum import Enum

class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"
    GUEST = "guest"

class UserData(BaseModel):
    email: str
    role: UserRole

@app.route('/users/{user_id}/permissions', methods=['POST'])
def set_permissions(
    user_id: int,           # Path parameter
    force: bool,            # Body parameter (primitive)
    notify: str = "email",  # Body parameter with default
    user_data: UserData     # Body parameter (complex object)
):
    return {"status": "permissions updated"}
```

**Generated Request Body:**
```json
{
  "force": true,
  "notify": "email",
  "email": "user@example.com",
  "role": "admin"
}
```

### Type Formats and Examples

Pyweber automatically generates appropriate examples and formats:

```python
from datetime import datetime
from uuid import UUID

class Event(BaseModel):
    id: UUID
    name: str
    start_date: datetime
    attendee_count: int
    is_public: bool

@app.route('/events', methods=['POST'])
def create_event(event: Event):
    return {"event_created": True}
```

**Generated OpenAPI Schema:**
```json
{
  "properties": {
    "id": {
      "type": "string",
      "format": "uuid",
      "example": "550e8400-e29b-41d4-a716-446655440000"
    },
    "start_date": {
      "type": "string",
      "format": "date-time",
      "example": "2023-12-25T14:30:00Z"
    },
    "attendee_count": {
      "type": "integer",
      "format": "int32",
      "example": 2147483647
    }
  }
}
```

## Documentation Access

### Swagger UI
Visit `http://localhost:8800/docs` to access the interactive Swagger UI interface.

### OpenAPI JSON
The raw OpenAPI specification is available at `http://localhost:8800/_pyweber/{uuid}/openapi.json`

*Note: UUID is automatically generated for cache-busting purposes.*

## Best Practices

### 1. Use Type Hints Consistently
```python
# ✅ Good
def create_user(name: str, age: int, user: User):
    pass

# ❌ Avoid
def create_user(name, age, user):
    pass
```

### 2. Provide Default Values
```python
class UserPreferences(BaseModel):
    theme: str = "light"
    language: str = "en"
    notifications: bool = True
```

### 3. Use Descriptive Route Names
```python
@app.route('/users/{user_id}', name='get_user_by_id', methods=['GET'])
def get_user(user_id: int):
    pass
```

### 4. Avoid *args and **kwargs
```python
# ❌ Not supported - will raise ValueError
def bad_route(*args, **kwargs):
    pass

# ✅ Use explicit parameters instead
def good_route(user_id: int, data: UserData):
    pass
```

## Error Handling

Pyweber provides clear error messages for unsupported patterns:

```python
# This will raise a helpful error:
@app.route('/bad-route')
def bad_route(**kwargs):
    pass

# Error: **kwargs parameter 'kwargs' not supported in route functions.
# Use explicit parameters or typed classes instead for OpenAPI documentation.
```

## Performance Considerations

- **Lazy Loading**: OpenAPI schema is generated only when accessed
- **Caching**: Schemas are cached per route for optimal performance
- **Memory Efficient**: Minimal overhead for type introspection
- **Zero Dependencies**: No additional packages required for basic functionality

## Migration from Other Frameworks

### From FastAPI
```python
# FastAPI
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

@app.post("/users/")
def create_user(user: User):
    return user

# Pyweber (almost identical!)
import pyweber as pw
from pydantic import BaseModel

app = pw.Pyweber()

@app.route('/users', methods=['POST'])
def create_user(user: User):
    return user
```

### From Flask
```python
# Flask (manual work)
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/users', methods=['POST'])
def create_user():
    data = request.get_json()
    user = User(**data)  # Manual instantiation
    return jsonify(user.dict())

# Pyweber (automatic!)
@app.route('/users', methods=['POST'])
def create_user(user: User):
    return user  # Automatic instantiation and serialization
```

## Conclusion

Pyweber's OpenAPI integration represents a **paradigm shift** in Python web framework design:

- **Developer First**: Focus on writing business logic, not boilerplate
- **Type Safe**: Leverage Python's type system for better code quality
- **Universal**: Works with any class structure you prefer
- **Zero Config**: Documentation that writes itself

Experience the future of Python web development with Pyweber's intelligent OpenAPI integration