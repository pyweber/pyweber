# Authentication

Lightweight session login helpers inspired by Flask-Login — **no ORM**. Pair them with your own user store (dict, SQLAlchemy, etc.).

For API-token auth see OpenAPI security schemes (`HTTPBearer`, `HTTPBasic`, API keys) in the security / OpenAPI docs. `@login_required` accepts **either** a signed login cookie **or** a successful `request.auth` from those schemes.

## Quick start

```python
import pyweber as pw
from pyweber.auth import (
    login_required, login_user, logout_user,
    current_user, hash_password, check_password,
    register_roles, permission_required, has_permission,
)

app = pw.Pyweber()

register_roles({
    'admin': ['*'],
    'editor': ['posts:read', 'posts:write'],
    'viewer': ['posts:read'],
})

# Example in-memory users (replace with a database)
USERS = {
    'alice': {'password': hash_password('secret'), 'roles': ['admin']},
    'bob': {'password': hash_password('secret'), 'roles': ['editor']},
}

@app.route('/login', methods=['GET', 'POST'])
def login(request: pw.Request):
    if request.method == 'GET':
        return '<form method="post">...</form>'
    # parse body...
    username, password = 'alice', 'secret'
    user = USERS.get(username)
    if not user or not check_password(password, user['password']):
        return pw.Response.json({'detail': 'Invalid credentials'}, status=401)
    login_user(username, roles=user['roles'], data={'name': username})
    return pw.Response(content='', status=302, headers={'Location': '/dashboard'})

@app.route('/dashboard')
@login_required(redirect='/login')
def dashboard():
    u = current_user()
    return f"<h1>Hello {u['id']}</h1>"

@app.route('/admin')
@login_required(roles=['admin'], redirect='/login')
def admin():
    return '<h1>Admin</h1>'

@app.route('/posts', methods=['POST'])
@permission_required('posts:write')
def create_post():
    return {'ok': True}

@app.route('/logout', methods=['POST'])
def logout():
    logout_user()
    return pw.Response(content='', status=302, headers={'Location': '/'})
```

Decorator order (Flask-style): put `@login_required` **closest to the function**, `@app.route` above it:

```python
@app.route('/dash')
@login_required(redirect='/login')
def dash():
    ...
```

## RBAC (roles & permissions)

1. **Register** role → permission maps once at startup (`register_roles` / `define_role`).
2. Pass **roles** on `login_user(...)`.
3. Gate handlers with `roles=` / `permissions=` (or the shorthand decorators).

| Gate | Meaning |
|------|---------|
| `roles=['admin', 'mod']` | user needs **any** of these roles |
| `roles_all=['staff', 'verified']` | user needs **all** of these roles |
| `permissions=['posts:write']` | any listed permission (via registry + optional `data['permissions']`) |
| `permissions_all=[...]` | all listed permissions |
| `@role_required('admin')` | shorthand for `roles=` |
| `@permission_required('posts:write')` | shorthand for `permissions=` |

Wildcards in the registry:

- `*` — full access
- `users:*` — matches `users:read`, `users:delete`, …

Helpers inside handlers / templates:

```python
from pyweber.auth import has_role, has_permission, user_permissions

if has_role('admin'):
    ...
if has_permission('posts:write'):
    ...
print(user_permissions())  # expanded set for current_user()
```

Extra one-off grants without a role: `login_user(id, roles=[...], data={'permissions': ['billing:view']})`.

## CSRF on login / POST forms

POST/PUT/PATCH/DELETE require a CSRF token (enabled by default). This is **double-submit**:

1. On any response the server sets cookie `pyweber_csrf` (automatic).
2. The **same** value must be sent back as form field `_csrf` or header `X-CSRF-Token`.

The browser does **not** invent this on submit. Use `Form(method='POST')` (injects `_csrf` via `get_csrf_token()`), or embed it yourself:

```python
from pyweber.auth import ...
from pyweber import get_csrf_token

@app.route('/login', methods=['GET', 'POST'])
def login(request):
    if request.method == 'GET':
        token = get_csrf_token()
        return f'<form method="post"><input type="hidden" name="_csrf" value="{token}">...</form>'
    ...
```

JSON APIs: send header `X-CSRF-Token` (and the cookie). Or disable with `PYWEBER_CSRF_ENABLED=false` / `[security] csrf_enabled = false` (not for browser form apps in production).

> **Note:** browsers often send `Content-Type: application/x-www-form-urlencoded; charset=UTF-8`. PyWeber strips parameters via `request.media_type` / `request.is_media(...)` so form fields (including `_csrf`) still parse.

## API

| Helper | Role |
|--------|------|
| `hash_password(password)` | Storeable `pbkdf2_sha256$…` hash (stdlib) |
| `check_password(password, encoded)` | Constant-time verify |
| `login_user(id, roles=…, data=…, max_age=…)` | Set signed HttpOnly cookie `pyweber_user` |
| `logout_user()` | Expire that cookie |
| `current_user()` / `get_user_id()` | Read cookie or map `request.auth` |
| `@login_required(...)` | Auth + optional RBAC gates |
| `register_roles` / `define_role` / `clear_roles` | Process-wide role registry |
| `has_role` / `has_all_roles` / `has_permission` / `user_permissions` | Checks |
| `@permission_required` / `@role_required` | Shorthand gates |

Unauthenticated:

- `redirect='/login'` + HTML `Accept` → **302** `Location`
- otherwise → **401** JSON `{detail: "Unauthorized"}`
- wrong roles/permissions → **403** JSON `{detail: "Forbidden"}`

## Protecting `/docs` (audit 3.18)

Docs are **off in production** by default (`expose_in_production=False`). When you keep them on, attach schemes:

```python
app = pw.Pyweber(
    openapi=pw.OpenAPIConfig(
        expose_in_production=True,
        security_schemes={'BearerAuth': pw.HTTPBearer(verify=verify)},
        docs_security=['BearerAuth'],
    )
)
```

## Upload MIME validation

Optional: set `PYWEBER_VALIDATE_UPLOADS=1` or `[security] validate_uploads = true` to sniff magic bytes on multipart files (raises `UploadValidationError` when invalid).

## SQLAlchemy User model

Install `pyweber[db]` (+ a driver extra). Auth stays cookie-based; the ORM only holds credentials.

```python
import pyweber as pw
from pyweber.db import db, Model
from pyweber.auth import (
    login_required, login_user, logout_user,
    hash_password, check_password,
)
from sqlalchemy import String, select
from sqlalchemy.orm import Mapped, mapped_column

app = pw.Pyweber()
db.init_app(app)

class User(Model):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    roles_csv: Mapped[str] = mapped_column(String(255), default='viewer')

@app.route('/login', methods=['POST'])
async def login(request: pw.Request):
    body = request.json or {}
    email, password = body.get('email'), body.get('password')
    async with db.session() as session:
        user = await session.scalar(select(User).where(User.email == email))
        if not user or not check_password(password or '', user.password_hash):
            return pw.Response.json({'detail': 'Invalid credentials'}, status=401)
        roles = [r for r in user.roles_csv.split(',') if r]
        login_user(str(user.id), roles=roles, data={'email': user.email})
    return pw.Response.json({'ok': True})

@app.route('/me')
@login_required()
async def me():
    from pyweber.auth import current_user
    return current_user()
```

Create the table with Alembic (`pyweber db init` / `revision` / `upgrade`) — see [Database](database.md).

## What this is not

No built-in user table. Optional ORM is `pyweber[db]`; optional shared WS session store is `pyweber[redis]` ([session backends](session-backends.md)). No argon2 by default — PBKDF2 via stdlib. RBAC here is the in-process role→permission registry (enough for most apps without a full Identity framework).
