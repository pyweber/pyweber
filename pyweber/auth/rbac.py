"""Lightweight role → permission registry (no ORM).

Define roles once, then gate routes with ``permissions=`` / helpers::

    from pyweber.auth import register_roles, has_permission, login_required

    register_roles({
        'admin': ['*'],
        'editor': ['posts:read', 'posts:write'],
        'viewer': ['posts:read'],
    })

    @app.route('/posts', methods=['POST'])
    @login_required(permissions=['posts:write'])
    def create_post():
        ...
"""

from __future__ import annotations

from typing import Any, Iterable

from pyweber.auth.session import current_user

# Wildcard: full access, or ``resource:*`` for a namespace.
ALL_PERMISSIONS = '*'


class RoleRegistry:
    """Map role names to permission strings."""

    def __init__(self) -> None:
        self._roles: dict[str, set[str]] = {}

    def clear(self) -> None:
        self._roles.clear()

    def role(self, name: str, permissions: Iterable[str] | None = None) -> None:
        self._roles[str(name)] = {str(p) for p in (permissions or [])}

    def register(self, mapping: dict[str, Iterable[str]]) -> None:
        for name, perms in mapping.items():
            self.role(name, perms)

    def get(self, name: str) -> set[str]:
        return set(self._roles.get(str(name), set()))

    def permissions_for(self, roles: Iterable[str] | None) -> set[str]:
        out: set[str] = set()
        for role in roles or []:
            out |= self.get(role)
        return out

    def has_permission(self, roles: Iterable[str] | None, permission: str) -> bool:
        return permission_matches(self.permissions_for(roles), permission)


def permission_matches(granted: Iterable[str], needed: str) -> bool:
    """Return True if ``needed`` is covered by ``granted`` (supports ``*`` / ``ns:*``)."""
    need = str(needed)
    have = {str(p) for p in granted}
    if ALL_PERMISSIONS in have or need in have:
        return True
    if ':' in need:
        ns = need.split(':', 1)[0]
        if f'{ns}:*' in have:
            return True
    return False


def permissions_match_any(granted: Iterable[str], needed: Iterable[str]) -> bool:
    return any(permission_matches(granted, p) for p in needed)


def permissions_match_all(granted: Iterable[str], needed: Iterable[str]) -> bool:
    return all(permission_matches(granted, p) for p in needed)


_registry = RoleRegistry()


def get_role_registry() -> RoleRegistry:
    return _registry


def register_roles(mapping: dict[str, Iterable[str]]) -> None:
    """Register or replace role → permission mappings (process-wide)."""
    _registry.register(mapping)


def define_role(name: str, permissions: Iterable[str] | None = None) -> None:
    _registry.role(name, permissions)


def clear_roles() -> None:
    """Clear the process-wide role registry (useful in tests)."""
    _registry.clear()


def _user_role_names(user: dict[str, Any] | None = None) -> list[str]:
    u = user if user is not None else current_user()
    if not u:
        return []
    return [str(r) for r in (u.get('roles') or [])]


def _direct_permissions(user: dict[str, Any] | None = None) -> set[str]:
    """Extra permissions stored on the session (``data['permissions']``)."""
    u = user if user is not None else current_user()
    if not u:
        return set()
    data = u.get('data') or {}
    raw = data.get('permissions') or []
    if isinstance(raw, str):
        return {raw}
    return {str(p) for p in raw}


def user_permissions(user: dict[str, Any] | None = None) -> set[str]:
    """Expanded permissions for the current (or given) user."""
    u = user if user is not None else current_user()
    if not u:
        return set()
    return _registry.permissions_for(_user_role_names(u)) | _direct_permissions(u)


def has_role(*roles: str, require_all: bool = False, user: dict[str, Any] | None = None) -> bool:
    """True if the user has any (default) or all of the given roles."""
    u = user if user is not None else current_user()
    if not u or not roles:
        return False
    have = {str(r) for r in (u.get('roles') or [])}
    need = {str(r) for r in roles}
    if require_all:
        return need <= have
    return bool(have & need)


def has_all_roles(*roles: str, user: dict[str, Any] | None = None) -> bool:
    return has_role(*roles, require_all=True, user=user)


def has_permission(
    *permissions: str,
    require_all: bool = False,
    user: dict[str, Any] | None = None,
) -> bool:
    """True if the user has any (default) or all of the given permissions."""
    if not permissions:
        return False
    granted = user_permissions(user)
    if require_all:
        return permissions_match_all(granted, permissions)
    return permissions_match_any(granted, permissions)


def user_has_roles(
    user: dict[str, Any],
    roles: list[str] | None = None,
    *,
    roles_all: list[str] | None = None,
) -> bool:
    if roles_all:
        if not has_role(*roles_all, require_all=True, user=user):
            return False
    if roles:
        if not has_role(*roles, require_all=False, user=user):
            return False
    return True


def user_has_permissions(
    user: dict[str, Any],
    permissions: list[str] | None = None,
    *,
    permissions_all: list[str] | None = None,
) -> bool:
    if permissions_all:
        if not has_permission(*permissions_all, require_all=True, user=user):
            return False
    if permissions:
        if not has_permission(*permissions, require_all=False, user=user):
            return False
    return True
