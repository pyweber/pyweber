"""Security helpers: HMAC signing, path confinement, secure filenames, settings."""

from __future__ import annotations

import hashlib
import hmac
import logging
import os
import re
import secrets
from functools import lru_cache
from typing import Iterable
from uuid import uuid4

logger = logging.getLogger(__name__)

PLACEHOLDER_SECRET = 'TOKEN_HEX'
DEFAULT_MAX_BODY_SIZE = 10 * 1024 * 1024  # 10 MiB
SESSION_COOKIE_NAME = 'pyweber_sid'
CSRF_COOKIE_NAME = 'pyweber_csrf'
CSRF_FORM_FIELD = '_csrf'
CSRF_HEADER = 'X-CSRF-Token'


def _config():
    from pyweber.config.config import config
    return config


def get_env() -> str:
    env = os.environ.get('PYWEBER_ENV') or _config().get('session', 'env') or 'development'
    return str(env).strip().lower()


def is_production() -> bool:
    return get_env() in {'production', 'prod'}


def get_secret_key() -> str:
    key = os.environ.get('PYWEBER_SECRET_KEY') or _config().get('session', 'secret_key') or ''
    key = str(key).strip()
    if not key or key == PLACEHOLDER_SECRET:
        if is_production():
            raise RuntimeError(
                "session.secret_key is unset or still the placeholder 'TOKEN_HEX'. "
                "Set a strong secret via config or PYWEBER_SECRET_KEY before running in production."
            )
        logger.warning(
            "Using ephemeral development secret_key; set session.secret_key or PYWEBER_SECRET_KEY."
        )
        return _ephemeral_dev_secret()
    return key


@lru_cache(maxsize=1)
def _ephemeral_dev_secret() -> str:
    return secrets.token_hex(32)


def sign_value(value: str, *, key: str | None = None) -> str:
    secret = (key or get_secret_key()).encode('utf-8')
    payload = str(value)
    signature = hmac.new(secret, payload.encode('utf-8'), hashlib.sha256).hexdigest()
    return f'{payload}.{signature}'


def unsign_value(signed: str, *, key: str | None = None) -> str | None:
    if not signed or '.' not in signed:
        return None
    payload, _, signature = signed.rpartition('.')
    if not payload or not signature:
        return None
    secret = (key or get_secret_key()).encode('utf-8')
    expected = hmac.new(secret, payload.encode('utf-8'), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, signature):
        return None
    return payload


def generate_session_id() -> str:
    return secrets.token_urlsafe(32)


def generate_csrf_token(*, key: str | None = None) -> str:
    raw = secrets.token_urlsafe(32)
    return sign_value(raw, key=key)


def verify_csrf_token(token: str, cookie_token: str | None = None, *, key: str | None = None) -> bool:
    if not token:
        return False
    unsigned = unsign_value(token, key=key)
    if unsigned is None:
        return False
    if cookie_token is not None:
        cookie_unsigned = unsign_value(cookie_token, key=key)
        if cookie_unsigned is None:
            return False
        return hmac.compare_digest(unsigned, cookie_unsigned)
    return True


def csrf_enabled() -> bool:
    env = os.environ.get('PYWEBER_CSRF_ENABLED')
    if env is not None:
        return env.strip().lower() in {'1', 'true', 'yes', 'on'}
    value = _config().get('security', 'csrf_enabled', default=True)
    if isinstance(value, str):
        return value.strip().lower() in {'1', 'true', 'yes', 'on'}
    return bool(value)


# Allows HTTPS CDNs (Bootstrap, Google Fonts, jsDelivr icons) while still
# blocking exotic schemes and clickjacking. Override with PYWEBER_CSP /
# [security].csp; set to "off" to omit the header.
DEFAULT_CSP = (
    "default-src 'self'; "
    "script-src 'self' 'unsafe-inline' https:; "
    "style-src 'self' 'unsafe-inline' https:; "
    "font-src 'self' data: https:; "
    "img-src 'self' data: https:; "
    "connect-src 'self' ws: wss: https:; "
    "frame-ancestors 'none'; "
    "base-uri 'self'; "
    "form-action 'self'"
)

_CSP_OFF = frozenset({'', '0', 'false', 'off', 'none', 'disable', 'disabled'})


def resolve_csp() -> str | None:
    """Return CSP header value, or None to omit the header.

    Precedence: ``PYWEBER_CSP`` env → ``[security].csp`` config → ``DEFAULT_CSP``.
    """
    raw = os.environ.get('PYWEBER_CSP')
    if raw is None:
        raw = _config().get('security', 'csp', default=None)
    if raw is None:
        return DEFAULT_CSP
    value = str(raw).strip()
    if value.lower() in _CSP_OFF:
        return None
    return value


def get_allowed_origins() -> set[str]:
    origins = _config().get('security', 'allowed_origins', default=None)
    if origins is None:
        origins = []
    if isinstance(origins, str):
        origins = [o.strip() for o in origins.split(',') if o.strip()]
    env_origins = os.environ.get('PYWEBER_ALLOWED_ORIGINS')
    if env_origins:
        origins = list(origins) + [o.strip() for o in env_origins.split(',') if o.strip()]
    return {str(o).rstrip('/') for o in origins if o}


def get_max_body_size() -> int:
    value = os.environ.get('PYWEBER_MAX_BODY_SIZE') or _config().get(
        'security', 'max_body_size', default=DEFAULT_MAX_BODY_SIZE
    )
    try:
        size = int(value)
    except (TypeError, ValueError):
        return DEFAULT_MAX_BODY_SIZE
    return size if size > 0 else DEFAULT_MAX_BODY_SIZE


def https_enabled() -> bool:
    value = _config().get('server', 'https_enabled', default=False)
    if isinstance(value, str):
        return value.strip().lower() in {'1', 'true', 'yes', 'on'}
    return bool(value)


def secure_filename(filename: str | None) -> str:
    if not filename:
        return f'{uuid4().hex}_file'
    name = os.path.basename(str(filename).replace('\\', '/'))
    name = re.sub(r'[^A-Za-z0-9_.\-]', '_', name).strip('._')
    if not name:
        name = 'file'
    return f'{uuid4().hex}_{name}'[:255]


def safe_join(base_dir: str, *paths: str) -> str | None:
    """Join paths under base_dir; return None if the result escapes the base."""
    if not base_dir:
        return None
    base = os.path.realpath(base_dir)
    # Reject absolute / drive / UNC segments outright (do not silently re-root them)
    for part in paths:
        if not part:
            continue
        normalized = part.replace('\\', '/')
        if (
            os.path.isabs(part)
            or normalized.startswith('/')
            or re.match(r'^[A-Za-z]:', part)
            or normalized.startswith('//')
        ):
            return None

    relative = os.path.join(*paths) if paths else ''
    target = os.path.realpath(os.path.join(base, relative.lstrip('/\\')))
    try:
        if os.path.commonpath([base, target]) != base:
            return None
    except ValueError:
        # Different drives on Windows
        return None
    return target


def resolve_under_roots(requested: str, roots: Iterable[str]) -> str | None:
    """Resolve a URL/path under one of the allowed root directories."""
    requested = (requested or '').replace('\\', '/')
    stripped = requested.lstrip('/')
    for root in roots:
        if not root:
            continue
        root_real = os.path.realpath(root)
        # If requested is a URL path with a prefix matching the root name
        candidate = safe_join(root_real, stripped)
        if candidate and os.path.isfile(candidate):
            return candidate
        # Also try stripping a single leading path segment that names the root folder
        root_name = os.path.basename(root_real.rstrip('/\\'))
        if stripped.startswith(f'{root_name}/') or stripped.startswith(f'{root_name}\\'):
            remainder = stripped[len(root_name) + 1 :]
            candidate = safe_join(root_real, remainder)
            if candidate and os.path.isfile(candidate):
                return candidate
    return None
