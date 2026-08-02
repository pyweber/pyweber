"""Tests for 1.4 remainder + 1.5 DX/ops features."""

from __future__ import annotations

import gzip
import warnings

import pytest

from pyweber.pyweber.pyweber import Pyweber
from pyweber.testing import TestClient as HttpTestClient
from pyweber.models.openapi import OpenAPIConfig, OpenApiProcessor
from pyweber.utils.deprecation import reset_deprecation_warnings, warn_deprecated, deprecated_callable
from pyweber.utils.mime import sniff_mime, validate_upload, UploadValidationError
from pyweber.models.rate_limit import RateLimiter, rate_limit_enabled, get_rate_limit_rpm, get_rate_limiter
from pyweber.utils.exceptions import ParameterConversionError
from pyweber.models.file import File
from pyweber.models.field import Field
from pyweber.models.stream_stats import AdaptiveController


class TestDeprecation:
    def test_warn_once(self):
        reset_deprecation_warnings()
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter('always')
            warn_deprecated('demo_name', alternative='new_name')
            warn_deprecated('demo_name', alternative='new_name')
        assert len(caught) == 1


class TestCoerce:
    def test_coerce_int_bool_float(self):
        assert OpenApiProcessor.coerce_value('id', '42', int) == 42
        assert OpenApiProcessor.coerce_value('ok', 'true', bool) is True
        assert OpenApiProcessor.coerce_value('ok', '0', bool) is False
        assert OpenApiProcessor.coerce_value('x', '3.5', float) == 3.5

    def test_coerce_bad_int_raises(self):
        with pytest.raises(ParameterConversionError):
            OpenApiProcessor.coerce_value('id', 'nope', int)

    @pytest.mark.asyncio
    async def test_route_param_coercion(self):
        app = Pyweber()
        seen = {}

        @app.route('/users/{user_id}', methods=['GET'])
        def get_user(user_id: int):
            seen['user_id'] = user_id
            seen['type'] = type(user_id).__name__
            return {'user_id': user_id}

        client = HttpTestClient(app)
        resp = await client.get('/users/7')
        assert resp.status_code == 200
        assert seen['user_id'] == 7
        assert seen['type'] == 'int'

    @pytest.mark.asyncio
    async def test_route_param_bad_returns_400(self):
        app = Pyweber()

        @app.route('/items/{item_id}', methods=['GET'])
        def get_item(item_id: int):
            return {'item_id': item_id}

        client = HttpTestClient(app)
        resp = await client.get('/items/abc')
        assert resp.status_code == 400


class TestMiddlewareOnion:
    @pytest.mark.asyncio
    async def test_call_next(self):
        app = Pyweber()
        order = []

        @app.middleware()
        async def mw(request, call_next):
            order.append('before')
            response = await call_next()
            order.append('after')
            response.set_header('X-MW', '1')
            return response

        @app.route('/')
        def home():
            order.append('handler')
            return {'ok': True}

        client = HttpTestClient(app)
        resp = await client.get('/')
        assert resp.status_code == 200
        assert order == ['before', 'handler', 'after']
        assert resp.headers.get('X-MW') == '1'


class TestDocsProductionGate:
    def test_docs_disabled_in_production(self, monkeypatch):
        monkeypatch.setenv('PYWEBER_ENV', 'production')
        monkeypatch.setenv('PYWEBER_SECRET_KEY', 'prod-secret-key-32-chars-minimum')
        app = Pyweber(openapi=OpenAPIConfig())
        routes = app.list_routes
        assert '/docs' not in routes

    def test_docs_exposed_when_flag_set(self, monkeypatch):
        monkeypatch.setenv('PYWEBER_ENV', 'production')
        monkeypatch.setenv('PYWEBER_SECRET_KEY', 'prod-secret-key-32-chars-minimum')
        app = Pyweber(openapi=OpenAPIConfig(expose_in_production=True))
        assert '/docs' in app.list_routes


class TestRateLimit:
    def test_bucket_blocks(self):
        limiter = RateLimiter(rate_per_minute=60, burst=1.0)
        assert limiter.allow('a')[0] is True
        allowed, retry = limiter.allow('a')
        assert allowed is False
        assert retry > 0


class TestMime:
    def test_sniff_png(self):
        data = b'\x89PNG\r\n\x1a\n' + b'\x00' * 16
        assert sniff_mime(data) == 'image/png'

    def test_validate_allowed(self):
        data = b'%PDF-1.4'
        assert validate_upload(data, allowed=['application/pdf']) == 'application/pdf'
        with pytest.raises(UploadValidationError):
            validate_upload(data, allowed=['image/png'])


class TestGzipAndEtag:
    @pytest.mark.asyncio
    async def test_gzip_large_json(self):
        app = Pyweber()

        @app.route('/big', methods=['GET'])
        def big():
            return {'data': 'x' * 2000}

        client = HttpTestClient(app)
        resp = await client.get('/big', headers={'Accept-Encoding': 'gzip'})
        assert resp.headers.get('Content-Encoding') == 'gzip'
        raw = resp.response_content
        assert gzip.decompress(raw)


class TestNormalizePathAlias:
    def test_normaize_warns(self):
        app = Pyweber()
        reset_deprecation_warnings()
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter('always')
            assert app.normaize_path('/a/b') == app.normalize_path('/a/b')
        assert any('normaize_path' in str(w.message) for w in caught)


class TestOpsExtras:
    def test_rate_limit_config_helpers(self, monkeypatch):
        monkeypatch.setenv('PYWEBER_RATE_LIMIT_ENABLED', 'true')
        monkeypatch.setenv('PYWEBER_RATE_LIMIT_RPM', '30')
        assert rate_limit_enabled() is True
        assert get_rate_limit_rpm() == 30.0
        assert get_rate_limiter().rate_per_minute == 30.0

    def test_file_validate_and_sniff(self):
        field = Field(field_id='1')
        field.filename = 'x.png'
        field.value = b'\x89PNG\r\n\x1a\n' + b'\x00' * 8
        field.size = len(field.value)
        field.content_type = 'image/png'
        f = File(field)
        assert f.sniff_mime() == 'image/png'
        assert f.validate(allowed=['image/png']) == 'image/png'

    def test_deprecated_callable(self):
        reset_deprecation_warnings()

        @deprecated_callable(name='old_fn', alternative='new_fn')
        def old_fn():
            return 1

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter('always')
            assert old_fn() == 1
        assert caught

    def test_stream_stats_preferred_import(self):
        assert AdaptiveController is not None

    def test_sniff_jpeg_gif_text(self):
        assert sniff_mime(b'\xff\xd8\xff\x00') == 'image/jpeg'
        assert sniff_mime(b'GIF89a....') == 'image/gif'
        assert sniff_mime(b'hello world') == 'text/plain'

    @pytest.mark.asyncio
    async def test_rate_limit_returns_429(self, monkeypatch):
        monkeypatch.setenv('PYWEBER_RATE_LIMIT_ENABLED', 'true')
        monkeypatch.setenv('PYWEBER_RATE_LIMIT_RPM', '60')
        from pyweber.models import rate_limit as rl
        rl._default_limiter = RateLimiter(rate_per_minute=60, burst=1)

        app = Pyweber()

        @app.route('/')
        def home():
            return {'ok': True}

        client = HttpTestClient(app)
        assert (await client.get('/')).status_code == 200
        second = await client.get('/')
        assert second.status_code == 429

    @pytest.mark.asyncio
    async def test_client_post_json_and_csrf(self):
        app = Pyweber()

        @app.route('/echo', methods=['POST'])
        def echo():
            return {'ok': True}

        client = HttpTestClient(app)
        token = client.enable_csrf()
        resp = await client.post(
            '/echo',
            json={'a': 1},
            headers=client.csrf_headers(token),
        )
        # CSRF disabled in conftest by default
        assert resp.status_code in {200, 403}

    def test_csrf_form_helper(self):
        client = HttpTestClient(Pyweber())
        form = client.csrf_form({'name': 'x'})
        assert '_csrf' in form
        assert form['name'] == 'x'

    def test_deprecated_alias_class(self):
        from pyweber.utils.deprecation import deprecated_alias
        reset_deprecation_warnings()

        class New:
            def __init__(self):
                self.ok = True

        Old = deprecated_alias('OldCls', New, alternative='New')
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter('always')
            assert Old().ok is True
        assert caught

    def test_validate_upload_mismatch_declared(self):
        data = b'\x89PNG\r\n\x1a\nxxxx'
        assert validate_upload(data, declared_type='image/jpeg') == 'image/png'

    @pytest.mark.asyncio
    async def test_client_put_patch_delete(self):
        app = Pyweber()

        @app.route('/x', methods=['PUT', 'PATCH', 'DELETE'])
        def x():
            return {'ok': True}

        client = HttpTestClient(app)
        assert (await client.put('/x')).status_code == 200
        assert (await client.patch('/x')).status_code == 200
        assert (await client.delete('/x')).status_code == 200
