"""Regressions for the issues reported against 1.8.2."""

from __future__ import annotations

import io
import logging
from unittest.mock import patch

import pytest

import pyweber as pw
from pyweber.models.request import ClientInfo, Request
from pyweber.models.response import Response
from pyweber.testing.client import TestClient
from pyweber.utils.types import ContentTypes


def _request(headers: str) -> Request:
    return Request(headers=headers, body=b'', client_info=ClientInfo(host='127.0.0.1', port=0))


@pytest.fixture
def app():
    return pw.Pyweber()


@pytest.mark.asyncio
async def test_to_route_with_state_query_param_redirects(app):
    @app.route('/b')
    def b():
        return 'b'

    @app.route('/a')
    def a():
        return app.to_route('/b')

    internal_names = (
        'state', 'redirect_route', 'redirect_path', 'route', 'callback', 'method',
        'request', 'status_code', 'middlewares', 'resp', 'template', 'kwargs', 'params',
    )
    for name in internal_names:
        response = await TestClient(app).get(f'/a?{name}=xyz')
        assert response.status_code == 302, name
        response = await TestClient(app).get(f'/b?{name}=xyz')
        assert response.status_code == 200, name


def test_request_cookies_keep_equals_in_value():
    request = _request(
        'GET / HTTP/1.1\r\nHost: t\r\nCookie: data=eyJhIjoxfQ==; plain=a=b; quoted="x y"\r\n\r\n'
    )
    assert request.cookies == {'data': 'eyJhIjoxfQ==', 'plain': 'a=b', 'quoted': 'x y'}


@pytest.mark.asyncio
async def test_template_status_code_returned_by_route_is_used(app):
    @app.route('/x')
    def x():
        return pw.Template(template='<p>erro</p>', status_code=400)

    @app.route('/created', status_code=201)
    def created():
        return pw.Template(template='<p>ok</p>')

    assert (await TestClient(app).get('/x')).status_code == 400
    assert (await TestClient(app).get('/created')).status_code == 201


@pytest.mark.asyncio
async def test_response_returned_by_route_keeps_app_cookies(app):
    @app.route('/login')
    def login():
        app.set_cookie(cookie_name='app_cookie', cookie_value='1')
        return Response(
            content={'ok': True},
            cookies={'route_cookie': 'route_cookie=2; Path=/;', 'app_cookie': 'app_cookie=route; Path=/;'},
        )

    response = await TestClient(app).get('/login')
    assert 'pyweber_sid' in response.cookies
    assert response.cookies['route_cookie'].startswith('route_cookie=2')
    assert response.cookies['app_cookie'].startswith('app_cookie=route')


@pytest.mark.asyncio
async def test_dynamic_json_is_not_publicly_cached(app):
    @app.route('/api/me', content_type=ContentTypes.json, process_response=False)
    def me():
        return {'token': 'secreto'}

    response = await TestClient(app).get('/api/me')
    assert 'public' not in str(response.headers.get('Cache-Control'))
    assert 'ETag' not in response.headers


@pytest.mark.asyncio
async def test_framework_static_files_are_still_cached(app):
    response = await TestClient(app).get('/_pyweber/static/favicon.ico')
    assert response.headers.get('Cache-Control') == 'public, max-age=3600'
    assert 'ETag' in response.headers


class TestCsrfExemptions:
    @pytest.fixture(autouse=True)
    def _csrf_on(self, monkeypatch):
        monkeypatch.setenv('PYWEBER_CSRF_ENABLED', 'true')
        monkeypatch.delenv('PYWEBER_CSRF_EXEMPT_PATHS', raising=False)

    @pytest.mark.asyncio
    async def test_route_flag(self, app):
        app.add_route('/oauth/token', template={'ok': True}, methods=['POST'],
                      content_type=ContentTypes.json, csrf_exempt=True)
        app.add_route('/form', template={'ok': True}, methods=['POST'], content_type=ContentTypes.json)
        client = TestClient(app)
        client.cookies['other'] = '1'
        assert (await client.post('/oauth/token', json={})).status_code == 200
        assert (await client.post('/form', json={})).status_code == 403

    @pytest.mark.asyncio
    async def test_config_paths(self, app, monkeypatch):
        monkeypatch.setenv('PYWEBER_CSRF_EXEMPT_PATHS', '/api/v1/, /hooks')
        app.add_route('/api/v1/items', template={'ok': True}, methods=['POST'], content_type=ContentTypes.json)
        client = TestClient(app)
        client.cookies['other'] = '1'
        assert (await client.post('/api/v1/items', json={})).status_code == 200

    @pytest.mark.asyncio
    async def test_bearer_without_cookies(self, app):
        app.add_route('/api/items', template={'ok': True}, methods=['POST'], content_type=ContentTypes.json)
        response = await TestClient(app).post(
            '/api/items', json={}, headers={'Authorization': 'Bearer abc'}
        )
        assert response.status_code == 200


def test_print_line_survives_cp1252_console():
    from pyweber.utils.utils import PrintLine

    raw = io.BytesIO()
    console = io.TextIOWrapper(raw, encoding='cp1252')
    with patch('sys.stdout', console):
        PrintLine(text='✨ Trying to start the project')
        console.flush()
    assert b'Trying to start the project' in raw.getvalue()


def test_dev_secret_key_persisted_and_warned_once(tmp_path, monkeypatch, caplog):
    from pyweber.utils import security

    monkeypatch.delenv('PYWEBER_SECRET_KEY', raising=False)
    config_file = tmp_path / '.pyweber' / 'config.toml'

    class Cfg:
        path = str(config_file)

        def get(self, *args, **kwargs):
            return ''

    monkeypatch.setattr(security, '_config', lambda: Cfg())
    security._ephemeral_dev_secret.cache_clear()
    try:
        with caplog.at_level(logging.WARNING, logger='pyweber.utils.security'):
            first = security.get_secret_key()
            security.get_secret_key()
        assert sum('development secret_key' in r.message for r in caplog.records) == 1

        stored = (tmp_path / '.pyweber' / security.DEV_SECRET_FILE).read_text(encoding='utf-8')
        assert stored == first
        assert security.DEV_SECRET_FILE in (tmp_path / '.pyweber' / '.gitignore').read_text(encoding='utf-8')

        security._ephemeral_dev_secret.cache_clear()
        assert security.get_secret_key() == first
    finally:
        security._ephemeral_dev_secret.cache_clear()
