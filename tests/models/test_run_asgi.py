import json

import pytest

from pyweber.models.run import encode_header, run_as_asgi
from pyweber.pyweber.pyweber import Pyweber
from pyweber.core.template import Template
import pyweber.models.run as run_module


@pytest.fixture(autouse=True)
def reset_ws_state():
    run_module.WS_RUNNING = False
    yield
    run_module.WS_RUNNING = False


@pytest.fixture
def asgi_app():
    app = Pyweber()
    app.add_route(
        route='/',
        template=Template(template='<html><body>ASGI OK</body></html>'),
        methods=['GET'],
    )
    return app


class TestEncodeHeader:
    def test_skips_ignored_headers_case_insensitive(self):
        headers = {
            'Content-Type': 'text/html',
            'Set-Cookie': {'a': 'a=1'},
            'Code': 200,
        }
        encoded = encode_header(headers, 'set-cookie', 'code')
        names = [h[0] for h in encoded]
        assert b'content-type' in names
        assert b'set-cookie' not in names
        assert b'code' not in names


class TestRunAsAsgiHttp:
    @pytest.mark.asyncio
    async def test_http_request_response_cycle(self, asgi_app):
        scope = {
            'type': 'http',
            'method': 'GET',
            'scheme': 'http',
            'http_version': '1.1',
            'raw_path': b'/',
            'query_string': b'',
            'headers': [(b'host', b'localhost:8800')],
        }
        body_chunks = [{'type': 'http.request', 'body': b'', 'more_body': False}]
        sent = []

        async def receive():
            return body_chunks.pop(0)

        async def send(message):
            sent.append(message)

        await run_as_asgi(scope, receive, send, app=asgi_app)

        start = next(m for m in sent if m['type'] == 'http.response.start')
        body = next(m for m in sent if m['type'] == 'http.response.body')

        assert start['status'] == 200
        assert b'ASGI OK' in body['body']

    @pytest.mark.asyncio
    async def test_http_with_set_cookie(self, asgi_app):
        def handler(request, **kwargs):
            asgi_app.set_cookie('token', 'secret')
            return Template(template='logged')

        asgi_app.add_route(route='/login', template=handler, methods=['GET'])

        scope = {
            'type': 'http',
            'method': 'GET',
            'scheme': 'http',
            'http_version': '1.1',
            'raw_path': b'/login',
            'query_string': b'',
            'headers': [(b'host', b'localhost:8800')],
        }

        async def receive():
            return {'type': 'http.request', 'body': b'', 'more_body': False}

        sent = []

        async def send(message):
            sent.append(message)

        await run_as_asgi(scope, receive, send, app=asgi_app)

        start = next(m for m in sent if m['type'] == 'http.response.start')
        cookie_headers = [h for h in start['headers'] if h[0] == b'set-cookie']
        assert any(b'token=secret' in h[1] for h in cookie_headers)

    @pytest.mark.asyncio
    async def test_lifespan_is_noop(self, asgi_app):
        scope = {'type': 'lifespan'}
        await run_as_asgi(scope, lambda: None, lambda m: None, app=asgi_app)


class TestRunFunction:
    def test_run_rejects_non_callable_target(self):
        from pyweber.models.run import run

        with pytest.raises(TypeError, match='callable'):
            run(target='not-callable')
