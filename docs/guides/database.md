# Database (SQLAlchemy + Alembic)

!!! tip "Added in 1.6.0"
    Optional extra — core `pip install pyweber` stays free of SQLAlchemy. Install `pyweber[db]` (+ a driver extra).

PyWeber does **not** ship an ORM in the core install. Persistence is an **optional extra** built on **SQLAlchemy 2.0 (async-first)** with a thin Flask-SQLAlchemy-style wrapper and **Alembic** for migrations.

```bash
pip install 'pyweber[db]' 'pyweber[db-sqlite]'   # local / CI
pip install 'pyweber[db]' 'pyweber[db-pg]'        # PostgreSQL
```

## Design decisions (ADR)


| Decision   | Choice                       | Rationale                                 |
| ---------- | ---------------------------- | ----------------------------------------- |
| Engine     | SQLAlchemy 2.0               | Multi-DB, mature async, Alembic-native    |
| Public API | Thin wrapper (`db`, `Model`) | Better DX; escape hatch to raw SQLAlchemy |
| I/O        | Async-first (`AsyncSession`) | Aligns with ASGI / Uvicorn                |
| Migrations | Alembic                      | Industry standard with SQLAlchemy         |
| Packaging  | Extras only                  | Core stays dependency-light               |


**Not chosen:** Tortoise (Aerich, not Alembic), Peewee (weak multi-DB/migrations), reinventing a custom ORM, SQLModel as the framework default (you may still use SQLModel on the same engine).

## Quick start

```python
from pyweber.db import db, Model
from sqlalchemy import String, select
from sqlalchemy.orm import Mapped, mapped_column
import pyweber as pw

app = pw.Pyweber()
db.init_app(app)  # reads PYWEBER_DATABASE_URL or [database] in config

class User(Model):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True)

@app.route('/users/{user_id}')
async def get_user(user_id: int):
    async with db.session() as session:
        user = await session.get(User, user_id)
        if not user:
            return pw.Response.json({'detail': 'Not found'}, status=404)
        return {'id': user.id, 'email': user.email}
```

You can always use SQLAlchemy directly:

```python
from sqlalchemy import select
async with db.session() as session:
    result = await session.scalars(select(User).where(User.email == email))
```



## Configuration

```toml
[database]
url = "sqlite+aiosqlite:///./app.db"
# url = "postgresql+asyncpg://user:pass@localhost/app"
echo = false
pool_size = 5
# auto_commit = false   # if true, commit at end of db.session() when no error
```

Environment (wins over config):


| Variable               | Meaning                   |
| ---------------------- | ------------------------- |
| `PYWEBER_DATABASE_URL` | Full SQLAlchemy async URL |
| `DATABASE_URL`         | Fallback alias            |




### Drivers (extras)


| Database        | Extra                | URL scheme                           |
| --------------- | -------------------- | ------------------------------------ |
| SQLite          | `pyweber[db-sqlite]` | `sqlite+aiosqlite:///./app.db`       |
| PostgreSQL      | `pyweber[db-pg]`     | `postgresql+asyncpg://...`           |
| MySQL / MariaDB | `pyweber[db-mysql]`  | `mysql+aiomysql://...`               |
| SQL Server      | `pyweber[db-mssql]`  | `mssql+aioodbc://...` (experimental) |




## Migrations (Alembic)

```bash
pyweber db init              # alembic.ini + migrations/ (async env)
pyweber db revision -m "add users"
pyweber db migrate           # apply all pending (same as upgrade head)
pyweber db upgrade head      # explicit target if needed
pyweber db downgrade -1
```

Point `migrations/env.py` at your models' metadata (`Model.metadata`). Hot-reload already skips `alembic` / `sqlalchemy` / `database` modules by default.

## Multi-database examples

Same API; only the URL (and optional driver extra) changes:

```toml
# SQLite (dev / CI)
[database]
url = "sqlite+aiosqlite:///./app.db"

# PostgreSQL
# url = "postgresql+asyncpg://app:secret@localhost:5432/app"

# MySQL / MariaDB
# url = "mysql+aiomysql://app:secret@localhost:3306/app"

# SQL Server (experimental)
# url = "mssql+aioodbc://app:secret@localhost/app?driver=ODBC+Driver+18+for+SQL+Server"
```

```bash
export PYWEBER_DATABASE_URL='postgresql+asyncpg://app:secret@db:5432/app'
```

Legacy `[database.database_1]` keys in older configs are still read when building a URL from `type` / `host` / `port` / `name`.

## Request lifecycle

- Prefer `async with db.session() as session:` inside **async** route handlers.
- Optional: `db.init_app(app, auto_middleware=True)` registers onion middleware that binds a request-scoped session (commit/rollback per `database.auto_commit`).
- Helpers: `await db.get(Model, id)` and `await db.scalars(select(...))` — thin wrappers; prefer raw SQLAlchemy when you need full control.



## ASGI vs built-in server


| Mode                     | Recommendation for DB apps                                                                                    |
| ------------------------ | ------------------------------------------------------------------------------------------------------------- |
| **ASGI (Uvicorn)**       | Preferred in production — native async I/O for `AsyncSession` and drivers                                     |
| **Built-in** `app.run()` | Fine for demos; async handlers still run on the event loop, but prefer ASGI once you use Postgres/MySQL pools |


Do **not** call blocking sync SQLAlchemy APIs from request handlers. If you must bridge sync code, use SQLAlchemy’s `await session.run_sync(...)` sparingly.

## Auth + User model

`pyweber.auth` stays ORM-agnostic. Hash passwords with `hash_password` / `check_password`, load the row via SQLAlchemy, then `login_user(...)`. Full example: [Authentication — SQLAlchemy User](authentication.md#sqlalchemy-user-model).

## See also

- [Session backends (memory / Redis)](session-backends.md)
- [Deployment](deployment.md) — ASGI, multi-replica
- [Environment variables](../environment.md)

