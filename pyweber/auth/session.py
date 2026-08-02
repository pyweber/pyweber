"""Signed login-user cookie (not the reactive WS session id)."""

from __future__ import annotations

import json
import time
from typing import Any

from pyweber.models.context import get_cookie_manager, get_current_request
from pyweber.utils.security import https_enabled, sign_value, unsign_value

USER_COOKIE_NAME = 'pyweber_user'
DEFAULT_MAX_AGE = 60 * 60 * 24 * 14  # 14 days


def _encode_payload(payload: dict[str, Any]) -> str:
    raw = json.dumps(payload, separators=(',', ':'), sort_keys=True)
    return sign_value(raw)


def _decode_payload(signed: str | None) -> dict[str, Any] | None:
    if not signed:
        return None
    raw = unsign_value(signed)
    if not raw:
        return None
    try:
        data = json.loads(raw)
    except (TypeError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict) or 'id' not in data:
        return None
    exp = data.get('exp')
    if exp is not None:
        try:
            if float(exp) < time.time():
                return None
        except (TypeError, ValueError):
            return None
    return data


def _from_request_auth() -> dict[str, Any] | None:
    request = get_current_request()
    auth = getattr(request, 'auth', None) if request else None
    if auth is None:
        return None
    user = getattr(auth, 'user', None)
    if isinstance(user, dict) and 'id' in user:
        roles = user.get('roles') or getattr(auth, 'scopes', None) or []
        return {
            'id': user['id'],
            'roles': list(roles) if roles else [],
            'data': {k: v for k, v in user.items() if k not in ('id', 'roles')},
            'scheme': getattr(auth, 'scheme', None),
        }
    if user is not None:
        return {
            'id': user,
            'roles': list(getattr(auth, 'scopes', None) or []),
            'data': {},
            'scheme': getattr(auth, 'scheme', None),
        }
    # credentials-only success (e.g. bearer token string)
    creds = getattr(auth, 'credentials', None)
    if creds is not None:
        return {
            'id': creds if not isinstance(creds, dict) else creds.get('id', creds),
            'roles': list(getattr(auth, 'scopes', None) or []),
            'data': creds if isinstance(creds, dict) else {},
            'scheme': getattr(auth, 'scheme', None),
        }
    return {
        'id': getattr(auth, 'scheme', 'authenticated'),
        'roles': list(getattr(auth, 'scopes', None) or []),
        'data': {},
        'scheme': getattr(auth, 'scheme', None),
    }


def current_user() -> dict[str, Any] | None:
    """Return the logged-in user dict, or map ``request.auth``, or None."""
    request = get_current_request()
    if request is not None:
        signed = request.cookies.get(USER_COOKIE_NAME)
        payload = _decode_payload(signed)
        if payload is not None:
            return {
                'id': payload['id'],
                'roles': list(payload.get('roles') or []),
                'data': dict(payload.get('data') or {}),
            }
    return _from_request_auth()


def get_user_id() -> Any | None:
    user = current_user()
    return None if user is None else user.get('id')


def login_user(
    user_id: Any,
    *,
    roles: list[str] | None = None,
    data: dict[str, Any] | None = None,
    max_age: int = DEFAULT_MAX_AGE,
) -> dict[str, Any]:
    """Mark the current request's principal as logged in (signed cookie)."""
    cm = get_cookie_manager()
    if cm is None:
        raise RuntimeError('login_user() must be called inside an HTTP request handler')

    now = time.time()
    payload = {
        'id': user_id,
        'roles': list(roles or []),
        'data': dict(data or {}),
        'exp': now + max_age if max_age and max_age > 0 else None,
    }
    signed = _encode_payload(payload)
    cm.set_cookie(
        cookie_name=USER_COOKIE_NAME,
        cookie_value=signed,
        httponly=True,
        secure=https_enabled(),
        samesite='Strict',
        max_age=max_age if max_age and max_age > 0 else None,
    )
    return {
        'id': user_id,
        'roles': list(roles or []),
        'data': dict(data or {}),
    }


def logout_user() -> None:
    """Clear the login cookie on the current response."""
    cm = get_cookie_manager()
    if cm is None:
        raise RuntimeError('logout_user() must be called inside an HTTP request handler')
    cm.delete_cookie(
        cookie_name=USER_COOKIE_NAME,
        httponly=True,
        secure=https_enabled(),
        samesite='Strict',
    )
