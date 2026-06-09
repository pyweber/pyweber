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

Hot reload watches Python files. Modules like `alembic` and `database` are skipped by default during reload to avoid breaking migrations.

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

- [ ] Set `debug = false` in config
- [ ] Use HTTPS in production
- [ ] Put a reverse proxy (nginx, Caddy) in front for static files if needed
- [ ] Do not rely on hot reload
- [ ] Configure session `secret_key` in config
- [ ] Test WebSocket connectivity through your proxy

## Platform notes


| Platform    | I/O selector |
| ----------- | ------------ |
| Linux       | epoll        |
| Windows     | select       |
| macOS / BSD | kqueue       |


The built-in server uses a non-blocking accept loop suitable for Linux production workloads.

## Next steps

- [Installation](../installation.md) — project setup
- [Environment variables](../environment.md) — configuration reference

