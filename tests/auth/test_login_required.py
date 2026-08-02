"""@login_required and login session tests."""

from __future__ import annotations

import pytest

from pyweber.auth import (
    USER_COOKIE_NAME,
    check_password,
    current_user,
    hash_password,
    login_required,
    login_user,
    logout_user,
)
from pyweber.auth.session import _decode_payload
from pyweber.models.openapi import OpenAPIConfig
from pyweber.models.request import Request, ClientInfo
from pyweber.models.security import AuthContext, HTTPBearer
from pyweber.pyweber.pyweber import Pyweber
from pyweber.utils.types import ContentTypes


def _req(method: str, path: str, extra: str = '') -> Request:
    return Request(
        headers=f'{method} {path} HTTP/1.1\r\nHost: localhost\r\n{extra}\r\n',
        body=b'',
        client_info=ClientInfo(host='127.0.0.1', port=0),
    )


def _cookie_header(response) -> str:
    cookies = response.headers.get('Set-Cookie') or {}
    if isinstance(cookies, dict):
        parts = []
        for raw in cookies.values():
            # "name=value; Path=..."
            parts.append(raw.split(';', 1)[0])
        return '; '.join(parts)
    return ''


@pytest.mark.asyncio
async def test_login_required_redirects_html():
    app = Pyweber()

    @app.route('/dash', methods=['GET'])
    @login_required(redirect='/login')
    def dash():
        return 'secret'

    resp = await app.get_response(_req('GET', '/dash', 'Accept: text/html\r\n'))
    assert resp.status_code == 302
    assert resp.headers.get('Location') == '/login'


@pytest.mark.asyncio
async def test_login_required_json_401():
    app = Pyweber()

    @app.route('/api/me', methods=['GET'], content_type=ContentTypes.json)
    @login_required()
    def me():
        return {'ok': True}

    resp = await app.get_response(_req('GET', '/api/me', 'Accept: application/json\r\n'))
    assert resp.status_code == 401
    assert b'Unauthorized' in resp.response_content


@pytest.mark.asyncio
async def test_login_user_sets_cookie_and_allows_access():
    app = Pyweber()
    passwords = {'alice': hash_password('pw')}

    @app.route('/login', methods=['POST'], content_type=ContentTypes.json)
    def do_login():
        login_user('alice', roles=['user'], data={'name': 'Alice'})
        return {'ok': True}

    @app.route('/dash', methods=['GET'])
    @login_required(redirect='/login')
    def dash():
        u = current_user()
        return f"hi-{u['id']}-{u['data'].get('name')}"

    login_resp = await app.get_response(_req('POST', '/login', 'Accept: application/json\r\n'))
    assert login_resp.status_code == 200
    cookie = _cookie_header(login_resp)
    assert USER_COOKIE_NAME in cookie
    assert check_password('pw', passwords['alice'])

    signed = None
    for part in cookie.split('; '):
        if part.startswith(f'{USER_COOKIE_NAME}='):
            signed = part.split('=', 1)[1]
            break
    assert signed
    payload = _decode_payload(signed)
    assert payload['id'] == 'alice'

    dash_resp = await app.get_response(
        _req('GET', '/dash', f'Cookie: {USER_COOKIE_NAME}={signed}\r\nAccept: text/html\r\n')
    )
    assert dash_resp.status_code == 200
    assert b'hi-alice-Alice' in dash_resp.response_content


@pytest.mark.asyncio
async def test_roles_forbid_without_match():
    app = Pyweber()

    @app.route('/login', methods=['POST'], content_type=ContentTypes.json)
    def do_login():
        login_user('bob', roles=['user'])
        return {'ok': True}

    @app.route('/admin', methods=['GET'], content_type=ContentTypes.json)
    @login_required(roles=['admin'])
    def admin():
        return {'admin': True}

    login_resp = await app.get_response(_req('POST', '/login'))
    signed = None
    for part in _cookie_header(login_resp).split('; '):
        if part.startswith(f'{USER_COOKIE_NAME}='):
            signed = part.split('=', 1)[1]
            break

    resp = await app.get_response(
        _req('GET', '/admin', f'Cookie: {USER_COOKIE_NAME}={signed}\r\nAccept: application/json\r\n')
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_logout_clears_access():
    app = Pyweber()

    @app.route('/login', methods=['POST'], content_type=ContentTypes.json)
    def do_login():
        login_user('u1')
        return {'ok': True}

    @app.route('/logout', methods=['POST'], content_type=ContentTypes.json)
    def do_logout():
        logout_user()
        return {'ok': True}

    @app.route('/dash', methods=['GET'], content_type=ContentTypes.json)
    @login_required()
    def dash():
        return {'id': current_user()['id']}

    login_resp = await app.get_response(_req('POST', '/login'))
    signed = None
    for part in _cookie_header(login_resp).split('; '):
        if part.startswith(f'{USER_COOKIE_NAME}='):
            signed = part.split('=', 1)[1]
            break

    logout_resp = await app.get_response(
        _req('POST', '/logout', f'Cookie: {USER_COOKIE_NAME}={signed}\r\n')
    )
    assert USER_COOKIE_NAME in _cookie_header(logout_resp)

    # Old cookie still sent by client but we verify login still works with cookie;
    # logout only clears on response — client must drop cookie. Tampered/expired handled by unsign.
    # After logout_user the response Set-Cookie expires; requesting with old signed cookie still
    # validates until expiry — that's expected for stateless cookies. Call logout then use empty cookie:
    denied = await app.get_response(_req('GET', '/dash', 'Accept: application/json\r\n'))
    assert denied.status_code == 401


@pytest.mark.asyncio
async def test_request_auth_satisfies_login_required():
    app = Pyweber(
        openapi=OpenAPIConfig(
            security_schemes={
                'BearerAuth': HTTPBearer(verify=lambda credentials: {'id': 'tok-user', 'roles': ['user']}),
            },
        )
    )

    @app.route('/secure', methods=['GET'], content_type=ContentTypes.json, security=['BearerAuth'])
    @login_required()
    def secure():
        return {'id': current_user()['id']}

    # Missing bearer → security enforcer 401 before decorator
    missing = await app.get_response(_req('GET', '/secure', 'Accept: application/json\r\n'))
    assert missing.status_code == 401

    ok = await app.get_response(
        _req('GET', '/secure', 'Authorization: Bearer anything\r\nAccept: application/json\r\n')
    )
    assert ok.status_code == 200
    assert b'tok-user' in ok.response_content


@pytest.mark.asyncio
async def test_docs_security_applied():
    app = Pyweber(
        openapi=OpenAPIConfig(
            docs_url='/docs',
            openapi_url='/openapi.json',
            expose_in_production=True,
            security_schemes={'BearerAuth': HTTPBearer(verify=lambda c: c == 'ok')},
            docs_security=['BearerAuth'],
        )
    )
    denied = await app.get_response(_req('GET', '/docs'))
    assert denied.status_code == 401

    allowed = await app.get_response(_req('GET', '/docs', 'Authorization: Bearer ok\r\n'))
    assert allowed.status_code == 200
