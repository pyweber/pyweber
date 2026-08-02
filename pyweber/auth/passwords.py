"""Password hashing helpers (stdlib PBKDF2-HMAC-SHA256)."""

from __future__ import annotations

import hashlib
import hmac
import secrets

DEFAULT_ITERATIONS = 260_000
_SCHEME = 'pbkdf2_sha256'


def hash_password(password: str, *, iterations: int = DEFAULT_ITERATIONS) -> str:
    """Hash a password for storage.

    Format: ``pbkdf2_sha256$<iterations>$<salt_hex>$<digest_hex>``
    """
    if not isinstance(password, str) or password == '':
        raise ValueError('password must be a non-empty string')
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        bytes.fromhex(salt),
        iterations,
    ).hex()
    return f'{_SCHEME}${iterations}${salt}${digest}'


def check_password(password: str, encoded: str) -> bool:
    """Constant-time verify of ``password`` against ``hash_password`` output."""
    if not password or not encoded or not isinstance(encoded, str):
        return False
    try:
        scheme, iter_s, salt, digest = encoded.split('$', 3)
    except ValueError:
        return False
    if scheme != _SCHEME:
        return False
    try:
        iterations = int(iter_s)
        salt_b = bytes.fromhex(salt)
        expected = bytes.fromhex(digest)
    except (TypeError, ValueError):
        return False
    actual = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt_b,
        iterations,
    )
    return hmac.compare_digest(actual, expected)
