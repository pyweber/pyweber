"""Security hardening unit tests (audit 1.4)."""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from pyweber.core.element import Element
from pyweber.models.response import Response
from pyweber.models.request import Request
from pyweber.utils.types import ContentTypes
from pyweber.utils.security import (
    CSRF_COOKIE_NAME,
    CSRF_FORM_FIELD,
    CSRF_HEADER,
    SESSION_COOKIE_NAME,
    generate_csrf_token,
    generate_session_id,
    get_allowed_origins,
    get_max_body_size,
    is_production,
    safe_join,
    secure_filename,
    sign_value,
    unsign_value,
    verify_csrf_token,
)
from pyweber.connection.websocket import WebsocketManager
from pyweber.pyweber.pyweber import Pyweber
from pyweber.components.form import Form


class TestSecurityCrypto:
    def test_sign_unsign_roundtrip(self):
        signed = sign_value('session-abc', key='test-secret')
        assert unsign_value(signed, key='test-secret') == 'session-abc'

    def test_unsign_rejects_tamper(self):
        signed = sign_value('session-abc', key='test-secret')
        tampered = signed[:-4] + 'dead'
        assert unsign_value(tampered, key='test-secret') is None

    def test_secure_filename_strips_traversal(self):
        name = secure_filename('../../etc/passwd')
        assert '..' not in name
        assert '/' not in name
        assert '\\' not in name
        assert name.endswith('_passwd')

    def test_safe_join_blocks_escape(self, tmp_path: Path):
        base = tmp_path / 'static'
        base.mkdir()
        (base / 'ok.txt').write_text('ok')
        assert safe_join(str(base), 'ok.txt') == str((base / 'ok.txt').resolve())
        assert safe_join(str(base), '../secret.txt') is None

    def test_csrf_double_submit(self):
        token = generate_csrf_token(key='csrf-secret')
        assert verify_csrf_token(token, token, key='csrf-secret')
        assert not verify_csrf_token(token, generate_csrf_token(key='csrf-secret'), key='csrf-secret')

    def test_is_production_env(self, monkeypatch):
        monkeypatch.setenv('PYWEBER_ENV', 'production')
        assert is_production() is True
        monkeypatch.setenv('PYWEBER_ENV', 'development')
        assert is_production() is False


class TestXSSEscape:
    def test_sanitize_default_escapes_content_and_attrs(self):
        el = Element(
            tag='input',
            content='<script>alert(1)</script>',
            value='" onmouseover="alert(1)',
            attrs={'title': '<b>x</b>'},
        )
        html = el.to_html()
        assert '<script>' not in html
        assert '&lt;script&gt;' in html
        assert 'onmouseover' not in html or '&quot;' in html
        assert '<b>' not in html

    def test_sanitize_false_allows_raw(self):
        el = Element(tag='div', content='<b>raw</b>', sanitize=False)
        assert '<b>raw</b>' in el.to_html()


class TestCORSAndHeaders:
    def _request(self, origin='https://evil.example'):
        request = Mock(spec=Request)
        request.method = 'GET'
        request.scheme = 'HTTP/1.1'
        request.path = '/'
        request.first_line = 'GET / HTTP/1.1'
        request.full_path = '/'
        request.origin = origin
        request.host = 'localhost'
        request.accept_control_request_headers = ''
        return request

    def test_cors_omitted_by_default(self):
        response = Response(
            request=self._request(),
            response_content=b'ok',
            code=200,
            cookies={},
            response_type=ContentTypes.html,
            route='/',
        )
        assert 'Access-Control-Allow-Origin' not in response.headers
        assert 'Access-Control-Allow-Credentials' not in response.headers
        assert response.headers['X-Content-Type-Options'] == 'nosniff'
        assert response.headers['X-Frame-Options'] == 'DENY'

    def test_cors_allows_whitelisted_origin(self, monkeypatch):
        monkeypatch.setenv('PYWEBER_ALLOWED_ORIGINS', 'https://app.example')
        response = Response(
            request=self._request(origin='https://app.example'),
            response_content=b'ok',
            code=200,
            cookies={},
            response_type=ContentTypes.json,
            route='/api',
        )
        assert response.headers['Access-Control-Allow-Origin'] == 'https://app.example'
        assert response.headers['Access-Control-Allow-Credentials'] == 'true'

    @pytest.mark.asyncio
    async def test_cors_preflight_options(self, monkeypatch):
        from pyweber.pyweber.pyweber import Pyweber

        monkeypatch.setenv('PYWEBER_ALLOWED_ORIGINS', 'https://app.example')
        app = Pyweber()
        request = Request(
            headers=(
                'OPTIONS /api HTTP/1.1\r\n'
                'Host: localhost\r\n'
                'Origin: https://app.example\r\n'
                'Access-Control-Request-Method: POST\r\n'
                'Access-Control-Request-Headers: content-type, authorization\r\n'
                '\r\n'
            ),
            body=b'',
        )
        response = await app.get_response(request)
        assert response.status_code == 204
        assert response.headers['Access-Control-Allow-Origin'] == 'https://app.example'
        assert 'content-type' in response.headers['Access-Control-Allow-Headers'].lower()


class TestSessionBinding:
    def test_ws_ignores_client_session_without_cookie(self):
        mgr = WebsocketManager.__new__(WebsocketManager)
        client_id = 'attacker-chosen-id'
        resolved = mgr.get_session_id(session_id=client_id, cookies={})
        assert resolved != client_id

    def test_ws_uses_signed_cookie(self):
        mgr = WebsocketManager.__new__(WebsocketManager)
        sid = generate_session_id()
        cookies = {SESSION_COOKIE_NAME: sign_value(sid, key='ws-secret')}
        with patch('pyweber.connection.websocket.unsign_value', side_effect=lambda v, key=None: unsign_value(v, key='ws-secret')):
            resolved = mgr.get_session_id(session_id='other', cookies=cookies)
        # Without patching get_secret_key consistently, re-sign with same key path:
        cookies = {SESSION_COOKIE_NAME: sign_value(sid)}
        resolved = mgr.get_session_id(session_id='other', cookies=cookies)
        assert resolved == sid


class TestStaticPathTraversal:
    def test_resolve_safe_static_blocks_traversal(self, tmp_path: Path):
        static = tmp_path / 'static'
        static.mkdir()
        (static / 'ok.css').write_text('body{}')
        secret = tmp_path / 'secret.txt'
        secret.write_text('secret')

        app = Pyweber(str(static))
        assert app.resolve_safe_static_path(f'/static/ok.css') is not None or \
            app.resolve_safe_static_path(str(static / 'ok.css')) is not None
        assert app.resolve_safe_static_path('/static/../secret.txt') is None


class TestCSRFEnforcement:
    @pytest.mark.asyncio
    async def test_post_without_csrf_returns_403(self, monkeypatch):
        monkeypatch.setenv('PYWEBER_CSRF_ENABLED', 'true')
        app = Pyweber()

        @app.route('/submit', methods=['POST'])
        def submit():
            return {'ok': True}

        request = Request(
            headers='POST /submit HTTP/1.1\r\nHost: localhost\r\nContent-Type: application/json\r\nContent-Length: 2\r\n\r\n',
            body=b'{}',
        )
        response = await app.get_response(request)
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_post_with_csrf_succeeds(self, monkeypatch):
        monkeypatch.setenv('PYWEBER_CSRF_ENABLED', 'true')
        app = Pyweber()

        @app.route('/submit', methods=['POST'])
        def submit():
            return {'ok': True}

        token = generate_csrf_token()
        headers = (
            f'POST /submit HTTP/1.1\r\n'
            f'Host: localhost\r\n'
            f'Content-Type: application/x-www-form-urlencoded\r\n'
            f'Cookie: {CSRF_COOKIE_NAME}={token}\r\n'
            f'{CSRF_HEADER}: {token}\r\n'
            f'Content-Length: 0\r\n\r\n'
        )
        request = Request(headers=headers, body=b'')
        response = await app.get_response(request)
        assert response.status_code == 200

    def test_form_injects_csrf_hidden(self, monkeypatch):
        monkeypatch.setenv('PYWEBER_CSRF_ENABLED', 'true')
        form = Form(method='POST', id='login')
        html = form.to_html()
        assert CSRF_FORM_FIELD in html
        assert 'type="hidden"' in html or "type='hidden'" in html or 'hidden' in html.lower()


class TestProductionErrors:
    @pytest.mark.asyncio
    async def test_production_hides_exception_details(self, monkeypatch):
        monkeypatch.setenv('PYWEBER_ENV', 'production')
        monkeypatch.setenv('PYWEBER_SECRET_KEY', 'prod-test-secret-key-32chars!!')
        app = Pyweber()

        @app.route('/boom')
        def boom():
            raise RuntimeError('sensitive database password=hunter2')

        request = Request(headers='GET /boom HTTP/1.1\r\nHost: localhost\r\n\r\n', body=b'')
        response = await app.get_response(request)
        body = response.response_content.decode('utf-8', errors='ignore')
        assert response.status_code == 500
        assert 'hunter2' not in body
        assert 'sensitive database' not in body


class TestSecurityHelpersExtra:
    def test_get_max_body_size_invalid_falls_back(self, monkeypatch):
        monkeypatch.setenv('PYWEBER_MAX_BODY_SIZE', 'not-a-number')
        assert get_max_body_size() == 10 * 1024 * 1024

    def test_get_allowed_origins_from_env(self, monkeypatch):
        monkeypatch.setenv('PYWEBER_ALLOWED_ORIGINS', 'https://a.example, https://b.example/')
        origins = get_allowed_origins()
        assert 'https://a.example' in origins
        assert 'https://b.example' in origins

    def test_file_secure_filename_helper(self):
        from pyweber.models.file import File
        name = File.secure_filename('..\\evil.exe')
        assert name.endswith('_evil.exe')
        assert '..' not in name

    def test_unsign_empty_and_bad_format(self):
        assert unsign_value('', key='k') is None
        assert unsign_value('nosig', key='k') is None
        assert unsign_value('.onlysig', key='k') is None

    def test_verify_csrf_without_cookie(self):
        token = generate_csrf_token(key='k')
        assert verify_csrf_token(token, None, key='k')
        assert not verify_csrf_token('', None, key='k')
        assert not verify_csrf_token('bad.token', None, key='k')

    def test_safe_join_absolute_escape(self, tmp_path: Path):
        base = tmp_path / 'root'
        base.mkdir()
        assert safe_join(str(base), 'C:\\Windows\\system32') is None
        assert safe_join(str(base), '/etc/passwd') is None

    @pytest.mark.asyncio
    async def test_session_cookie_issued_on_get(self):
        app = Pyweber()

        @app.route('/')
        def home():
            return '<html><body>hi</body></html>'

        request = Request(headers='GET / HTTP/1.1\r\nHost: localhost\r\n\r\n', body=b'')
        response = await app.get_response(request)
        cookies = response.cookies
        assert isinstance(cookies, dict)
        assert any(SESSION_COOKIE_NAME in str(v) for v in cookies.values())

    def test_load_static_files_respects_roots(self, tmp_path: Path):
        from pyweber.utils.loads import LoadStaticFiles
        allowed = tmp_path / 'allowed'
        allowed.mkdir()
        (allowed / 'a.txt').write_text('hello')
        outside = tmp_path / 'outside.txt'
        outside.write_text('nope')
        data = LoadStaticFiles(path=str(allowed / 'a.txt'), allowed_roots=[str(allowed)]).load
        assert 'hello' in data
        with pytest.raises(FileNotFoundError):
            LoadStaticFiles(path=str(outside), allowed_roots=[str(allowed)]).load


class TestResolveUnderRootsAndSecrets:
    def test_resolve_under_roots_finds_file(self, tmp_path: Path):
        from pyweber.utils.security import resolve_under_roots

        root = tmp_path / 'static'
        root.mkdir()
        (root / 'app.css').write_text('body{}')
        found = resolve_under_roots('static/app.css', [str(root)])
        assert found is not None
        assert found.endswith('app.css')
        assert resolve_under_roots('missing.css', [str(root)]) is None
        assert resolve_under_roots('', [str(root)]) is None
        assert resolve_under_roots('x', ['']) is None

    def test_resolve_under_roots_with_prefix_strip(self, tmp_path: Path):
        from pyweber.utils.security import resolve_under_roots

        root = tmp_path / 'assets'
        root.mkdir()
        (root / 'logo.png').write_text('png')
        # path includes root folder name as prefix
        found = resolve_under_roots(f'assets/logo.png', [str(root)])
        assert found is not None

    def test_get_secret_key_production_raises(self, monkeypatch):
        from pyweber.utils.security import get_secret_key, PLACEHOLDER_SECRET

        monkeypatch.setenv('PYWEBER_ENV', 'production')
        monkeypatch.delenv('PYWEBER_SECRET_KEY', raising=False)
        with patch('pyweber.utils.security._config') as cfg:
            cfg.return_value.get.return_value = PLACEHOLDER_SECRET
            with pytest.raises(RuntimeError, match='secret_key'):
                get_secret_key()

    def test_get_secret_key_dev_ephemeral(self, monkeypatch):
        from pyweber.utils.security import get_secret_key, _ephemeral_dev_secret

        monkeypatch.setenv('PYWEBER_ENV', 'development')
        monkeypatch.delenv('PYWEBER_SECRET_KEY', raising=False)
        _ephemeral_dev_secret.cache_clear()
        with patch('pyweber.utils.security._config') as cfg:
            cfg.return_value.get.return_value = ''
            key = get_secret_key()
            assert isinstance(key, str) and len(key) >= 32

    def test_https_enabled_string(self):
        from pyweber.utils.security import https_enabled

        with patch('pyweber.utils.security._config') as cfg:
            cfg.return_value.get.return_value = 'true'
            assert https_enabled() is True
            cfg.return_value.get.return_value = 'off'
            assert https_enabled() is False
            cfg.return_value.get.return_value = True
            assert https_enabled() is True

    def test_secure_filename_empty_and_none(self):
        assert secure_filename(None).endswith('_file')
        assert secure_filename('').endswith('_file')
        assert secure_filename('...').endswith('_file') or '_file' in secure_filename('...')

    def test_csrf_enabled_from_config_string(self, monkeypatch):
        from pyweber.utils.security import csrf_enabled

        monkeypatch.delenv('PYWEBER_CSRF_ENABLED', raising=False)
        with patch('pyweber.utils.security._config') as cfg:
            cfg.return_value.get.return_value = 'yes'
            assert csrf_enabled() is True
            cfg.return_value.get.return_value = 'no'
            assert csrf_enabled() is False
            cfg.return_value.get.return_value = True
            assert csrf_enabled() is True

    def test_get_allowed_origins_from_config_string(self, monkeypatch):
        monkeypatch.delenv('PYWEBER_ALLOWED_ORIGINS', raising=False)
        with patch('pyweber.utils.security._config') as cfg:
            cfg.return_value.get.return_value = 'https://a.example, https://b.example'
            origins = get_allowed_origins()
            assert 'https://a.example' in origins

    def test_safe_join_empty_base(self):
        assert safe_join('') is None

    def test_verify_csrf_mismatched_cookie(self):
        token = generate_csrf_token(key='k')
        other = generate_csrf_token(key='k')
        assert not verify_csrf_token(token, other, key='k')
        assert not verify_csrf_token(token, 'not.signed', key='k')

    def test_get_allowed_origins_none_config(self, monkeypatch):
        monkeypatch.delenv('PYWEBER_ALLOWED_ORIGINS', raising=False)
        with patch('pyweber.utils.security._config') as cfg:
            cfg.return_value.get.return_value = None
            assert get_allowed_origins() == set()

    def test_resolve_under_roots_basename_prefix(self, tmp_path: Path):
        from pyweber.utils.security import resolve_under_roots

        root = tmp_path / 'public'
        root.mkdir()
        (root / 'x.js').write_text('1')
        # Force the basename-prefix branch: path starts with root folder name
        found = resolve_under_roots('public/x.js', [str(root)])
        assert found is not None
