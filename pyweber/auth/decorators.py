"""``@login_required`` / ``@permission_required`` / ``@role_required``."""

from __future__ import annotations

import inspect
from functools import wraps
from typing import Any, Callable

from pyweber.auth.rbac import user_has_permissions, user_has_roles
from pyweber.auth.session import current_user
from pyweber.models.context import get_current_request
from pyweber.models.response import Response
from pyweber.utils.types import ContentTypes


def _wants_json(request) -> bool:
    if request is None:
        return False
    accept = (request.headers.get('accept') or '').lower()
    if 'application/json' in accept:
        if 'text/html' not in accept:
            return True
        return accept.find('application/json') <= accept.find('text/html')
    return False


def _unauthorized(*, redirect: str | None, request) -> Response:
    if redirect and not _wants_json(request):
        return Response(
            content=b'',
            status=302,
            request=request,
            route=redirect,
            headers={'Location': redirect},
            content_type=ContentTypes.txt,
        )
    return Response.json({'detail': 'Unauthorized'}, status=401, request=request)


def _forbidden(*, request) -> Response:
    return Response.json({'detail': 'Forbidden'}, status=403, request=request)


def _authorize(
    user: dict[str, Any] | None,
    *,
    roles: list[str] | None,
    roles_all: list[str] | None,
    permissions: list[str] | None,
    permissions_all: list[str] | None,
) -> str | None:
    """Return ``'unauthorized'``, ``'forbidden'``, or ``None`` if allowed."""
    if user is None:
        return 'unauthorized'
    if not user_has_roles(user, roles, roles_all=roles_all):
        return 'forbidden'
    if not user_has_permissions(user, permissions, permissions_all=permissions_all):
        return 'forbidden'
    return None


def _wrap_handler(
    func: Callable,
    *,
    redirect: str | None,
    roles: list[str] | None,
    roles_all: list[str] | None,
    permissions: list[str] | None,
    permissions_all: list[str] | None,
):
    if inspect.iscoroutinefunction(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            request = get_current_request()
            decision = _authorize(
                current_user(),
                roles=roles,
                roles_all=roles_all,
                permissions=permissions,
                permissions_all=permissions_all,
            )
            if decision == 'unauthorized':
                return _unauthorized(redirect=redirect, request=request)
            if decision == 'forbidden':
                return _forbidden(request=request)
            return await func(*args, **kwargs)

        return async_wrapper

    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        request = get_current_request()
        decision = _authorize(
            current_user(),
            roles=roles,
            roles_all=roles_all,
            permissions=permissions,
            permissions_all=permissions_all,
        )
        if decision == 'unauthorized':
            return _unauthorized(redirect=redirect, request=request)
        if decision == 'forbidden':
            return _forbidden(request=request)
        return func(*args, **kwargs)

    return sync_wrapper


def login_required(
    fn: Callable | None = None,
    *,
    redirect: str | None = None,
    roles: list[str] | None = None,
    roles_all: list[str] | None = None,
    permissions: list[str] | None = None,
    permissions_all: list[str] | None = None,
):
    """Require a logged-in user (cookie) or ``request.auth`` from OpenAPI schemes.

    RBAC (optional)::

        @login_required(roles=['admin', 'moderator'])          # any role
        @login_required(roles_all=['staff', 'verified'])       # all roles
        @login_required(permissions=['posts:write'])           # via register_roles()
        @login_required(permissions_all=['posts:read', 'posts:write'])

    Usage::

        @app.route('/dash')
        @login_required(redirect='/login')
        def dash():
            ...

        @login_required  # bare form
        def api_me():
            ...
    """

    def decorator(func: Callable):
        return _wrap_handler(
            func,
            redirect=redirect,
            roles=roles,
            roles_all=roles_all,
            permissions=permissions,
            permissions_all=permissions_all,
        )

    if fn is not None and callable(fn):
        return decorator(fn)
    return decorator


def permission_required(
    *permissions: str,
    redirect: str | None = None,
    require_all: bool = False,
):
    """Shorthand for ``@login_required(permissions=…)`` / ``permissions_all=``.

    ::

        @permission_required('posts:write')
        def create(): ...

        @permission_required('a', 'b', require_all=True)
        def both(): ...
    """
    if not permissions:
        raise TypeError('permission_required() needs at least one permission')
    perms = list(permissions)
    return login_required(
        redirect=redirect,
        permissions=None if require_all else perms,
        permissions_all=perms if require_all else None,
    )


def role_required(
    *roles: str,
    redirect: str | None = None,
    require_all: bool = False,
):
    """Shorthand for ``@login_required(roles=…)`` / ``roles_all=``.

    ::

        @role_required('admin')
        def admin_panel(): ...

        @role_required('staff', 'verified', require_all=True)
        def staff_only(): ...
    """
    if not roles:
        raise TypeError('role_required() needs at least one role')
    rs = list(roles)
    return login_required(
        redirect=redirect,
        roles=None if require_all else rs,
        roles_all=rs if require_all else None,
    )
