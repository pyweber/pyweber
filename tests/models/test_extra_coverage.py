"""Quick coverage for security schemes, mime, passwords, http, routes helpers."""

from __future__ import annotations

import base64
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from helpers import RecvSocket, make_http_request, make_ws_upgrade_request
from pyweber.auth.passwords import check_password, hash_password
from pyweber.connection.http import HttpServer
from pyweber.models.request import ClientInfo, Request
from pyweber.models.routes import Route
from pyweber.models.security import (
    APIKeyCookie,
    APIKeyHeader,
    APIKeyQuery,
    AuthContext,
    ForbiddenError,
    HTTPBasic,
    HTTPBearer,
    SecurityChallenge,
    SecurityEnforcer,
    SecurityError,
    SecurityScheme,
    normalize_security_requirements,
)
from pyweber.utils.mime import UploadValidationError, sniff_mime, validate_upload


def _req(method='GET', path='/', extra=''):
    return Request(
        headers=f'{method} {path} HTTP/1.1\r\nHost: localhost\r\n{extra}\r\n',
        body=b'',
        client_info=ClientInfo(host='127.0.0.1', port=1),
    )


class TestSecuritySchemesUnit:
    def test_base_scheme_abstract(self):
        s = SecurityScheme()
        with pytest.raises(NotImplementedError):
            s.to_openapi()
        with pytest.raises(NotImplementedError):
            s.extract(_req())
        assert s.www_authenticate() is None

    def test_errors_and_challenge(self):
        assert SecurityError().status_code == 401
        assert ForbiddenError().status_code == 403
        err = SecurityError('x', status_code=418)
        assert err.status_code == 418
        ch = SecurityChallenge(ok=True, auth=AuthContext(scheme='bearer', credentials='t'))
        assert ch.ok and ch.auth.scheme == 'bearer'

    def test_bearer_extract_and_openapi(self):
        scheme = HTTPBearer(description='tok', bearer_format='JWT')
        assert 'bearerFormat' in scheme.to_openapi()
        assert scheme.extract(_req()) is None
        assert scheme.extract(_req(extra='Authorization: Token x\r\n')) is None
        assert scheme.extract(_req(extra='Authorization: Bearer \r\n')) is None
        assert scheme.extract(_req(extra='Authorization: Bearer abc\r\n')) == 'abc'
        assert scheme.www_authenticate() == 'Bearer'

    def test_basic_extract(self):
        scheme = HTTPBasic(description='basic')
        assert 'basic' in scheme.to_openapi()['scheme']
        assert scheme.extract(_req()) is None
        assert scheme.extract(_req(extra='Authorization: Bearer x\r\n')) is None
        assert scheme.extract(_req(extra='Authorization: Basic !!!\r\n')) is None
        bad = base64.b64encode(b'nouserpass').decode()
        assert scheme.extract(_req(extra=f'Authorization: Basic {bad}\r\n')) is None
        good = base64.b64encode(b'u:p').decode()
        assert scheme.extract(_req(extra=f'Authorization: Basic {good}\r\n')) == ('u', 'p')
        assert 'Basic realm' in scheme.www_authenticate()

    def test_api_key_variants(self):
        h = APIKeyHeader(name='X-Key', description='k')
        assert h.to_openapi()['name'] == 'X-Key'
        assert h.extract(_req(extra='X-Key: secret\r\n')) == 'secret'
        assert h.extract(_req()) is None

        q = APIKeyQuery(name='key', description='q')
        assert q.to_openapi()['in'] == 'query'
        req = _req(path='/?key=abc')
        assert q.extract(req) == 'abc'

        c = APIKeyCookie(name='sid', description='c')
        assert c.to_openapi()['in'] == 'cookie'
        req2 = _req(extra='Cookie: sid=cookieval\r\n')
        assert c.extract(req2) == 'cookieval'

    def test_enforcer_and_normalize(self):
        assert normalize_security_requirements(None) is None
        assert normalize_security_requirements([]) == []
        assert normalize_security_requirements(['Bearer']) == [{'Bearer': []}]
        assert normalize_security_requirements([{'Bearer': ['a']}]) == [{'Bearer': ['a']}]
        with pytest.raises(TypeError):
            normalize_security_requirements([1])

        scheme = HTTPBearer(verify=lambda credentials, **kw: credentials == 'ok')
        enforcer = SecurityEnforcer({'Bearer': scheme})
        assert enforcer.enforce(_req(), []).ok
        fail = enforcer.enforce(_req(), [{'Bearer': []}])
        assert not fail.ok
        ok = enforcer.enforce(
            _req(extra='Authorization: Bearer ok\r\n'),
            [{'Bearer': []}],
        )
        assert ok.ok
        unknown = enforcer.enforce(_req(), [{'Missing': []}])
        assert not unknown.ok
        assert 'Unknown' in unknown.detail

        def forbid(credentials, **kw):
            raise ForbiddenError('no')

        enf2 = SecurityEnforcer({'Bearer': HTTPBearer(verify=forbid)})
        ch = enf2.enforce(
            _req(extra='Authorization: Bearer x\r\n'),
            [{'Bearer': []}],
        )
        assert ch.status_code == 403


class TestMimeAndPasswords:
    def test_sniff_and_validate(self):
        assert sniff_mime(None) is None
        assert sniff_mime(b'') is None
        assert sniff_mime(b'\x89PNG\r\n\x1a\nxxxx') == 'image/png'
        assert sniff_mime(b'\xff\xd8\xffabc') == 'image/jpeg'
        assert sniff_mime(b'GIF89a') == 'image/gif'
        assert sniff_mime(b'%PDF-1.4') == 'application/pdf'
        assert sniff_mime(b'PK\x03\x04') == 'application/zip'
        assert sniff_mime(b'RIFF....WEBP....') == 'image/webp'
        assert sniff_mime(b'RIFF....XXXX') is None or sniff_mime(b'RIFF....XXXX') == 'text/plain'
        assert sniff_mime(b'hello') == 'text/plain'
        assert sniff_mime(b'\xff\xfe\x00\x01') is None

        assert validate_upload(b'\x89PNG\r\n\x1a\n', allowed=['image/png']) == 'image/png'
        with pytest.raises(UploadValidationError):
            validate_upload(b'\x89PNG\r\n\x1a\n', allowed=['image/jpeg'])
        assert validate_upload(b'\xff\xfe', declared_type='text/plain', allowed=['text/plain']) == 'text/plain'
        assert validate_upload(b'\x89PNG\r\n\x1a\n', declared_type='image/jpeg') == 'image/png'
        assert validate_upload(b'\xff\xfe\x00', declared_type='application/octet-stream')

    def test_password_edge_cases(self):
        with pytest.raises(ValueError):
            hash_password('')
        h = hash_password('secret')
        assert check_password('secret', h)
        assert not check_password('', h)
        assert not check_password('secret', 'bad')
        assert not check_password('secret', 'other$1$ab$cd')
        assert not check_password('secret', 'pbkdf2_sha256$nope$zz$yy')


class TestHttpAndRoutesHelpers:
    @pytest.mark.asyncio
    async def test_handle_http_sends_response(self, pyweber_app):
        server = HttpServer()
        server.app = pyweber_app
        server.timeout = 1
        raw = make_http_request('GET', '/')
        client = RecvSocket(raw)
        await server.handle_http(client)
        assert client.closed
        assert client.sent  # response bytes

    @pytest.mark.asyncio
    async def test_handle_http_empty_headers(self, pyweber_app):
        server = HttpServer()
        server.app = pyweber_app
        with patch.object(server, 'process_request', AsyncMock(return_value=(None, None))):
            client = RecvSocket(b'')
            await server.handle_http(client)
            assert client.closed

    @pytest.mark.asyncio
    async def test_handle_websocket_error_path(self, pyweber_app):
        server = HttpServer()
        server.app = pyweber_app
        with patch.object(server, 'process_request', AsyncMock(side_effect=RuntimeError('boom'))):
            client = RecvSocket(make_ws_upgrade_request())
            await server.handle_websocket(client)
            assert client.closed

    def test_accept_clients_blocking_break(self, pyweber_app):
        server = HttpServer()
        server.app = pyweber_app

        class FakeSock:
            def accept(self):
                raise BlockingIOError()

        server._accept_clients(FakeSock())

    def test_route_query_parameters(self):
        def handler(user_id, q='x'):
            return q

        params = Route.get_query_parameters('/users/{user_id}', handler)
        assert 'user_id' in params['parameters']
        assert params['body']

        params2 = Route.get_query_parameters('/items/{missing}', lambda **kw: None)
        assert 'missing' in params2['parameters']
        assert Route.get_group(None) == Route.default_group()
        assert 'GET' in Route.default_method()
        assert 'POST' in Route.allowed_methods()
        assert Route.allowed_methods()
