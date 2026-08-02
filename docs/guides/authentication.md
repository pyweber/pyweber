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

## What this is not

No built-in user table / ORM, Redis-backed sessions, or argon2 by default — bring your own store. RBAC here is the in-process role→permission registry above (enough for most apps without a full Identity framework).
