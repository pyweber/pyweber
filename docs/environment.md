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
| `PYWEBER_WS_PORT` | Port for the WebSocket server | `8765` | `PYWEBER_WS_PORT=8766` |

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
python main.py
```