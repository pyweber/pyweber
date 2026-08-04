# PyWeber Environment Variables

PyWeber supports configuration through environment variables, allowing you to override settings without modifying configuration files. This is particularly useful for deployment environments, CI/CD pipelines, and development workflows.

## Available Environment Variables

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `PYWEBER_RELOAD_MODE` | Enable or disable hot reload for development | `False` | `PYWEBER_RELOAD_MODE=True` |
| `PYWEBER_HTTPS_ENABLED` | Enable or disable HTTPS for secure connections | `False` | `PYWEBER_HTTPS_ENABLED=True` |
| `PYWEBER_CERT_FILE` | Path to SSL certificate file for HTTPS | `None` | `PYWEBER_CERT_FILE=/path/to/cert.pem` |
| `PYWEBER_KEY_FILE` | Path to SSL key file for HTTPS | `None` | `PYWEBER_KEY_FILE=/path/to/key.pem` |
| `PYWEBER_SERVER_HOST` | Host address for the HTTP server | `127.0.0.1` | `PYWEBER_SERVER_HOST=0.0.0.0` |
| `PYWEBER_SERVER_PORT` | Port for the HTTP server | `8800` | `PYWEBER_SERVER_PORT=8080` |
| `PYWEBER_ENV` | Runtime environment (`development` / `production`) | `development` | `PYWEBER_ENV=production` |
| `PYWEBER_SECRET_KEY` | HMAC secret for session/CSRF cookies (overrides config) | from `session.secret_key` | `PYWEBER_SECRET_KEY=...` |
| `PYWEBER_ALLOWED_ORIGINS` | Comma-separated CORS allowlist | empty (no CORS) | `PYWEBER_ALLOWED_ORIGINS=https://app.example` |
| `PYWEBER_MAX_BODY_SIZE` | Max request body size in bytes | `10485760` | `PYWEBER_MAX_BODY_SIZE=2097152` |
| `PYWEBER_CSRF_ENABLED` | Enable CSRF checks on mutating HTTP methods | `true` | `PYWEBER_CSRF_ENABLED=false` |
| `PYWEBER_CSP` | Override `Content-Security-Policy` (`off` to disable) | CDN-friendly default | `PYWEBER_CSP=off` |
| `PYWEBER_VALIDATE_UPLOADS` | Sniff MIME magic bytes on multipart uploads | `false` | `PYWEBER_VALIDATE_UPLOADS=1` |
| `PYWEBER_DATABASE_URL` | SQLAlchemy async URL (`pyweber[db]`) | from `[database]` | `postgresql+asyncpg://…` |
| `DATABASE_URL` | Fallback alias for DB URL | — | same as above |
| `PYWEBER_SESSION_BACKEND` | WS session store: `memory` / `redis` | `memory` | `PYWEBER_SESSION_BACKEND=redis` |
| `PYWEBER_REDIS_URL` | Redis URL for session store | from `session.redis_url` | `redis://localhost:6379/0` |
| `REDIS_URL` | Fallback alias for Redis URL | — | same as above |
| `PYWEBER_ALLOWED_REDIRECT_HOSTS` | Hosts allowed for absolute `Window.open` / `to_url` / `launch_url` | empty (relative `/…` only) | `app.example,cdn.example` |

!!! tip "Added in 1.6.0"
    `PYWEBER_DATABASE_URL`, `PYWEBER_SESSION_BACKEND`, `PYWEBER_REDIS_URL` (and `DATABASE_URL` / `REDIS_URL` aliases).

!!! tip "Added in 1.6.0.dev2"
    `PYWEBER_ALLOWED_REDIRECT_HOSTS` / `[security].allowed_redirect_hosts` — open-redirect hardening.
## Security config (`config.toml`)

```toml
[session]
secret_key = 'replace-me'
env = 'development'   # use 'production' to hide 500 details
timeout = 3600
backend = 'memory'    # or 'redis' with pyweber[redis]
# redis_url = 'redis://localhost:6379/0'

[database]
# url = 'sqlite+aiosqlite:///./app.db'
# echo = false

[security]
allowed_origins = []  # e.g. ['https://app.example']
max_body_size = 10485760
csrf_enabled = true
# csp = 'off'  # or a full policy string; PYWEBER_CSP env overrides this
```

- Cross-origin browser apps must list origins in `allowed_origins` (CORS is off by default).
- Default CSP allows `'self'`, `'unsafe-inline'`, and `https:` for scripts/styles/fonts/images so Bootstrap/Google Fonts/jsDelivr work. Tighten via `PYWEBER_CSP` / `[security].csp` in production if you self-host assets.
- `Element` escapes HTML by default; use `sanitize=False` only for trusted markup.
- Save uploads with `secure_filename(file.filename)` (filenames from multipart are already sanitized).

## Usage

### Setting Environment Variables

#### On Linux/macOS:
```bash
export PYWEBER_RELOAD_MODE=True
export PYWEBER_HTTPS_ENABLED=True
export PYWEBER_CERT_FILE=.pyweber/certs/localhost.pem
export PYWEBER_KEY_FILE=.pyweber/certs/localhost-key.pem
python main.py
```

#### On Windows:
```cmd
set PYWEBER_RELOAD_MODE=True
set PYWEBER_HTTPS_ENABLED=True
set PYWEBER_CERT_FILE=.pyweber\certs\localhost.pem
set PYWEBER_KEY_FILE=.pyweber\certs\localhost-key.pem
python main.py
```

### Using with CLI

The PyWeber CLI automatically sets environment variables based on command-line arguments:

```bash
# Run with hot reload
pyweber run --reload

# Run with HTTPS using auto-generated certificate
pyweber run --https --auto-cert

# Run with HTTPS using specific certificate files
pyweber run --https --cert /path/to/cert.pem --key /path/to/key.pem
```

## Priority Order

When determining configuration values, PyWeber uses the following priority order:

1. Environment variables (highest priority)
2. Command-line arguments
3. Configuration file values
4. Default values (lowest priority)

This means environment variables will always override settings in your configuration files.

## Security Considerations

- Store sensitive information (like API keys or database credentials) in environment variables rather than configuration files
- Never commit certificate private keys to version control
- For production environments, use properly signed certificates from trusted certificate authorities
- When using self-signed certificates in development, be aware of browser security warnings

## Examples

### Development with Hot Reload and HTTPS

```bash
export PYWEBER_RELOAD_MODE=True
export PYWEBER_HTTPS_ENABLED=True
export PYWEBER_CERT_FILE=.pyweber/certs/localhost.pem
export PYWEBER_KEY_FILE=.pyweber/certs/localhost-key.pem
python main.py
```

### Production Configuration

```bash
export PYWEBER_RELOAD_MODE=False
export PYWEBER_HTTPS_ENABLED=True
export PYWEBER_CERT_FILE=/etc/letsencrypt/live/yourdomain.com/fullchain.pem
export PYWEBER_KEY_FILE=/etc/letsencrypt/live/yourdomain.com/privkey.pem
export PYWEBER_SERVER_HOST=0.0.0.0
export PYWEBER_ENV=production
export PYWEBER_DATABASE_URL='postgresql+asyncpg://app:secret@db:5432/app'
export PYWEBER_SESSION_BACKEND=redis
export PYWEBER_REDIS_URL='redis://redis:6379/0'
uvicorn main:app --host 0.0.0.0 --port 8000
```