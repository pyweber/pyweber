# Session backends (memory / Redis)

Reactive WebSocket sessions (`connection.session.Session`) default to an **in-process memory** store. That is fine for a single worker; horizontal scale needs a shared backend.

```bash
pip install 'pyweber[redis]'
```

## Design

```text
SessionManager (local cache + API)
        │
        ▼
  SessionStore protocol
     ├── MemorySessionStore   (default)
     └── RedisSessionStore    (optional extra)
```

- **Local cache** always holds live `Template` / `Window` objects for the current process.
- **Redis** stores a **serializable snapshot** (`session_id`, `current_route`, `create_at`, `template_html`) so another worker can hydrate a session after a miss.
- Window state on another process starts empty (client reconnect refreshes it). Prefer **sticky sessions** *or* Redis for multi-replica WS.

## Configuration

```toml
[session]
secret_key = 'replace-me'
timeout = 3600
backend = 'memory'          # or 'redis'
redis_url = 'redis://localhost:6379/0'
# key_prefix = 'pyweber:session:'
```

| Variable | Meaning |
|----------|---------|
| `PYWEBER_SESSION_BACKEND` | `memory` / `redis` |
| `PYWEBER_REDIS_URL` | Redis URL (also used if `redis_url` empty) |
| `REDIS_URL` | Fallback alias |

TTL for Redis keys follows `session.timeout` (seconds).

## Programmatic setup

```python
from pyweber.session_store import configure_session_store

configure_session_store(backend='redis', redis_url='redis://localhost:6379/0', ttl=3600)
```

Or rely on config at import / first use via `configure_session_store_from_config()`.

## Multi-replica notes

1. **Sticky sessions** at the load balancer — memory backend is enough.
2. **Redis backend** — any worker can hydrate template HTML after miss; still recommend sticky for fewer hydrations.
3. Auth cookies (`pyweber.auth`) are independent of this store; they use signed HTTP cookies.

## Auth vs reactive sessions

- **`pyweber.auth`** (`login_user` cookie) is independent of this store.
- Pairing ORM users with login: [Authentication — SQLAlchemy User](authentication.md#sqlalchemy-user-model).

Cache / rate-limit sharing via Redis is **out of scope** for this MVP (future work).
