"""Lightweight session login helpers (Flask-Login style, no ORM) + RBAC."""

from pyweber.auth.decorators import login_required, permission_required, role_required
from pyweber.auth.passwords import check_password, hash_password
from pyweber.auth.rbac import (
    RoleRegistry,
    clear_roles,
    define_role,
    get_role_registry,
    has_all_roles,
    has_permission,
    has_role,
    register_roles,
    user_permissions,
)
from pyweber.auth.session import (
    USER_COOKIE_NAME,
    current_user,
    get_user_id,
    login_user,
    logout_user,
)

__all__ = [
    'USER_COOKIE_NAME',
    'RoleRegistry',
    'check_password',
    'clear_roles',
    'current_user',
    'define_role',
    'get_role_registry',
    'get_user_id',
    'has_all_roles',
    'has_permission',
    'has_role',
    'hash_password',
    'login_required',
    'login_user',
    'logout_user',
    'permission_required',
    'register_roles',
    'role_required',
    'user_permissions',
]
