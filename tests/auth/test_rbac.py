"""RBAC registry and permission gates."""

from __future__ import annotations

import pytest

from pyweber.auth import (
    USER_COOKIE_NAME,
    clear_roles,
    has_permission,
    has_role,
    login_required,
    login_user,
    permission_required,
    register_roles,
    role_required,
    user_permissions,
)
from pyweber.models.request import ClientInfo, Request
from pyweber.pyweber.pyweber import Pyweber
from pyweber.utils.types import ContentTypes


def _req(method: str, path: str, extra: str = '') -> Request:
    return Request(
        headers=f'{method} {path} HTTP/1.1\r\nHost: localhost\r\n{extra}\r\n',
        body=b'',
        client_info=ClientInfo(host='127.0.0.1', port=0),
    )


def _signed_cookie(response) -> str | None:
    cookies = response.headers.get('Set-Cookie') or {}
    if not isinstance(cookies, dict):
        return None
    for raw in cookies.values():
        part = raw.split(';', 1)[0]
        if part.startswith(f'{USER_COOKIE_NAME}='):
            return part.split('=', 1)[1]
    return None


@pytest.fixture(autouse=True)
def _reset_roles():
    clear_roles()
    yield
    clear_roles()


def test_register_roles_and_helpers():
    register_roles({
        'admin': ['*'],
        'editor': ['posts:read', 'posts:write'],
        'viewer': ['posts:read'],
    })
    assert has_permission('posts:write', user={'id': 'e', 'roles': ['editor'], 'data': {}})
    assert not has_permission('posts:write', user={'id': 'v', 'roles': ['viewer'], 'data': {}})
    assert has_permission('anything', user={'id': 'a', 'roles': ['admin'], 'data': {}})
    assert has_role('editor', user={'id': 'e', 'roles': ['editor'], 'data': {}})
    assert 'posts:read' in user_permissions({'id': 'v', 'roles': ['viewer'], 'data': {}})


def test_namespace_wildcard_and_direct_permissions():
    register_roles({'ops': ['users:*']})
    assert has_permission('users:delete', user={'id': 'o', 'roles': ['ops'], 'data': {}})
    assert not has_permission('posts:read', user={'id': 'o', 'roles': ['ops'], 'data': {}})
    assert has_permission(
        'billing:view',
        user={'id': 'x', 'roles': [], 'data': {'permissions': ['billing:view']}},
    )


@pytest.mark.asyncio
async def test_permission_required_allows_editor():
    register_roles({'editor': ['posts:write']})
    app = Pyweber()

    @app.route('/login', methods=['POST'], content_type=ContentTypes.json)
    def do_login():
        login_user('ed', roles=['editor'])
        return {'ok': True}

    @app.route('/posts', methods=['POST'], content_type=ContentTypes.json)
    @permission_required('posts:write')
    def create():
        return {'created': True}

    login_resp = await app.get_response(_req('POST', '/login'))
    signed = _signed_cookie(login_resp)
    assert signed
    ok = await app.get_response(
        _req('POST', '/posts', f'Cookie: {USER_COOKIE_NAME}={signed}\r\nAccept: application/json\r\n')
    )
    assert ok.status_code == 200
    assert b'created' in ok.response_content


@pytest.mark.asyncio
async def test_permission_required_forbids_viewer():
    register_roles({
        'editor': ['posts:write'],
        'viewer': ['posts:read'],
    })
    app = Pyweber()

    @app.route('/login', methods=['POST'], content_type=ContentTypes.json)
    def do_login():
        login_user('v', roles=['viewer'])
        return {'ok': True}

    @app.route('/posts', methods=['POST'], content_type=ContentTypes.json)
    @login_required(permissions=['posts:write'])
    def create():
        return {'created': True}

    login_resp = await app.get_response(_req('POST', '/login'))
    signed = _signed_cookie(login_resp)
    denied = await app.get_response(
        _req('POST', '/posts', f'Cookie: {USER_COOKIE_NAME}={signed}\r\nAccept: application/json\r\n')
    )
    assert denied.status_code == 403


@pytest.mark.asyncio
async def test_role_required_and_roles_all():
    app = Pyweber()

    @app.route('/login', methods=['POST'], content_type=ContentTypes.json)
    def do_login():
        login_user('s', roles=['staff'])
        return {'ok': True}

    @app.route('/staff', methods=['GET'], content_type=ContentTypes.json)
    @role_required('staff', 'admin')
    def staff():
        return {'ok': True}

    @app.route('/vip', methods=['GET'], content_type=ContentTypes.json)
    @login_required(roles_all=['staff', 'verified'])
    def vip():
        return {'vip': True}

    login_resp = await app.get_response(_req('POST', '/login'))
    signed = _signed_cookie(login_resp)
    assert (
        await app.get_response(
            _req('GET', '/staff', f'Cookie: {USER_COOKIE_NAME}={signed}\r\nAccept: application/json\r\n')
        )
    ).status_code == 200
    assert (
        await app.get_response(
            _req('GET', '/vip', f'Cookie: {USER_COOKIE_NAME}={signed}\r\nAccept: application/json\r\n')
        )
    ).status_code == 403


def test_permission_required_needs_args():
    with pytest.raises(TypeError):
        permission_required()
    with pytest.raises(TypeError):
        role_required()


def test_helpers_without_user_and_require_all():
    from pyweber.auth import define_role, get_role_registry, has_all_roles

    assert not has_role('admin')
    assert not has_permission('x')
    assert user_permissions() == set()

    define_role('staff', ['a', 'b'])
    assert get_role_registry().has_permission(['staff'], 'a')
    user = {'id': 'u', 'roles': ['staff'], 'data': {}}
    assert has_all_roles('staff', user=user)
    assert has_permission('a', 'b', require_all=True, user=user)
    assert not has_permission('a', 'missing', require_all=True, user=user)


@pytest.mark.asyncio
async def test_permissions_all_and_role_required_all():
    register_roles({'editor': ['posts:read', 'posts:write']})
    app = Pyweber()

    @app.route('/login', methods=['POST'], content_type=ContentTypes.json)
    def do_login():
        login_user('ed', roles=['editor'])
        return {'ok': True}

    @app.route('/both', methods=['GET'], content_type=ContentTypes.json)
    @permission_required('posts:read', 'posts:write', require_all=True)
    def both():
        return {'ok': True}

    @app.route('/need-two-roles', methods=['GET'], content_type=ContentTypes.json)
    @role_required('editor', 'admin', require_all=True)
    def need_two():
        return {'ok': True}

    signed = _signed_cookie(await app.get_response(_req('POST', '/login')))
    assert (
        await app.get_response(
            _req('GET', '/both', f'Cookie: {USER_COOKIE_NAME}={signed}\r\nAccept: application/json\r\n')
        )
    ).status_code == 200
    assert (
        await app.get_response(
            _req(
                'GET',
                '/need-two-roles',
                f'Cookie: {USER_COOKIE_NAME}={signed}\r\nAccept: application/json\r\n',
            )
        )
    ).status_code == 403
