# Deployment and running in production

Pyweber can run with its **built-in HTTP + WebSocket server** or as an **ASGI app** behind Uvicorn/Gunicorn.

## Development (built-in server)

```bash
pyweber run --reload
# or
python main.py
```

```python
import pyweber as pw

app = pw.Pyweber()

@app.route('/')
def home():
    return pw.Element('h1', content='Hello')

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8800, reload=True)
```

Hot reload watches Python files. Modules like `alembic`, `sqlalchemy`, and `database` are skipped by default during reload to avoid breaking migrations.

## ASGI (Uvicorn / Gunicorn)

Expose the app as ASGI:

```python
# main.py
import pyweber as pw

app = pw.Pyweber()

@app.route('/')
def home():
    return pw.Element('h1', content='Production')

# ASGI callable
asgi_app = app  # Pyweber implements __call__(scope, receive, send)
```

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

Or use the helper:

```python
from pyweber import run_as_asgi
run_as_asgi(app, host='0.0.0.0', port=8000)
```

!!! note "WebSocket + ASGI"
    Real-time updates require WebSocket support. Ensure your ASGI server and reverse proxy allow WebSocket upgrades on the same host/port.

## Database and Redis

Apps using `pyweber.db` should run under **ASGI** in production (`AsyncSession` + async drivers). See [Database](database.md).

```bash
pip install 'pyweber[db]' 'pyweber[db-pg]'
export PYWEBER_DATABASE_URL='postgresql+asyncpg://...'
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 2
```

Multiple workers / replicas:

| Concern | Approach |
|---------|----------|
| HTTP auth cookie | Signed cookie — works across workers (shared `secret_key`) |
| Reactive WS session | Sticky sessions **or** `session.backend = 'redis'` ([session backends](session-backends.md)) |
| Migrations | Run `pyweber db migrate` once before rolling out new workers |

## HTTPS

Configure certificates via environment variables or config file:


| Variable                | Purpose          |
| ----------------------- | ---------------- |
| `PYWEBER_HTTPS_ENABLED` | Enable TLS       |
| `PYWEBER_CERT_FILE`     | Certificate path |
| `PYWEBER_KEY_FILE`      | Private key path |


CLI helpers:

```bash
pyweber cert check-mkcert
pyweber cert mkcert
```

See [Environment variables](../environment.md) for the full list.

## Static assets

```python
app = pw.Pyweber('static')           # constructor
app.static('assets', 'images')       # or method — multiple dirs allowed
```

Only registered directories are served. This prevents accidental exposure of the whole project tree.

## Production checklist

- [ ] Set `debug = false` / `PYWEBER_ENV=production` in config
- [ ] Use HTTPS in production
- [ ] Put a reverse proxy (nginx, Caddy) in front for static files if needed
- [ ] Do not rely on hot reload
- [ ] Configure session `secret_key` (and Redis URL if `backend = 'redis'`)
- [ ] Set `PYWEBER_DATABASE_URL` when using the ORM; run Alembic before deploy
- [ ] Prefer Uvicorn/Gunicorn ASGI for DB-backed apps
- [ ] Test WebSocket connectivity through your proxy (sticky sessions or Redis store)

## Platform notes


| Platform    | I/O selector |
| ----------- | ------------ |
| Linux       | epoll        |
| Windows     | select       |
| macOS / BSD | kqueue       |


The built-in server uses a non-blocking accept loop suitable for Linux production workloads.

## Next steps

- [Installation](../installation.md) — project setup
- [Database](database.md) — SQLAlchemy + Alembic
- [Session backends](session-backends.md) — memory / Redis
- [Environment variables](../environment.md) — configuration reference

