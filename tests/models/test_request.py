import json
import pytest

from pyweber.models.request import Request, ClientInfo, RequestMode
from pyweber.utils.types import ContentTypes


WSGI_HEADERS = (
    'GET /api/users?page=1 HTTP/1.1\r\n'
    'Host: localhost:8800\r\n'
    'Cookie: session=abc; user=joao\r\n'
    'Accept: text/html\r\n\r\n'
)


class TestRequestWsgi:
    @pytest.fixture
    def wsgi_request(self):
        return Request(
            headers=WSGI_HEADERS,
            body=b'',
            client_info=ClientInfo(host='127.0.0.1', port=54321),
        )

    def test_parses_method_and_path(self, wsgi_request):
        assert wsgi_request.method == 'GET'
        assert wsgi_request.path == '/api/users'
        assert wsgi_request.request_mode == RequestMode.wsgi

    def test_query_params(self, wsgi_request):
        assert wsgi_request.query_params['page'] == '1'

    def test_cookies(self, wsgi_request):
        assert wsgi_request.cookies['session'] == 'abc'
        assert wsgi_request.cookies['user'] == 'joao'

    def test_full_path(self, wsgi_request):
        assert wsgi_request.full_path == '/api/users?page=1'

    def test_client_info(self, wsgi_request):
        assert wsgi_request.client_info.host == '127.0.0.1'
        assert wsgi_request.client_info.port == 54321


class TestRequestAsgi:
    def test_asgi_mode(self):
        scope = {
            'type': 'http',
            'method': 'POST',
            'scheme': 'http',
            'http_version': '1.1',
            'raw_path': b'/submit',
            'query_string': b'name=test',
            'headers': [
                (b'content-type', ContentTypes.json.value.encode()),
                (b'host', b'localhost'),
            ],
        }
        body = json.dumps({'ok': True}).encode()
        request = Request(headers=scope, body=body, client_info=ClientInfo(host='127.0.0.1', port=80))

        assert request.request_mode == RequestMode.asgi
        assert request.method == 'POST'
        assert request.path == '/submit'
        assert request.body == {'ok': True}


class TestContentTypeCharset:
    """Browsers append ``; charset=UTF-8`` — must not break body / CSRF parsing."""

    def test_form_urlencoded_with_charset(self):
        headers = (
            'POST /login HTTP/1.1\r\n'
            'Host: localhost\r\n'
            'Content-Type: application/x-www-form-urlencoded; charset=UTF-8\r\n\r\n'
        )
        request = Request(
            headers=headers,
            body=b'_csrf=tok&user=alice',
            client_info=ClientInfo(host='127.0.0.1', port=0),
        )
        assert request.content_type == 'application/x-www-form-urlencoded; charset=UTF-8'
        assert request.media_type == 'application/x-www-form-urlencoded'
        assert request.is_media(ContentTypes.form_encode)
        assert request.body['_csrf'] == 'tok'
        assert request.body['user'] == 'alice'

    def test_json_with_charset(self):
        headers = (
            'POST /api HTTP/1.1\r\n'
            'Host: localhost\r\n'
            'Content-Type: application/json; charset=UTF-8\r\n\r\n'
        )
        request = Request(
            headers=headers,
            body=json.dumps({'a': 1}).encode(),
            client_info=ClientInfo(host='127.0.0.1', port=0),
        )
        assert request.is_media('application/json', ContentTypes.json)
        assert request.body == {'a': 1}

    @pytest.mark.asyncio
    async def test_csrf_post_with_charset_content_type(self, monkeypatch):
        monkeypatch.setenv('PYWEBER_CSRF_ENABLED', 'true')
        monkeypatch.setenv('PYWEBER_SECRET_KEY', 'charset-csrf-secret-key-32bytes!!')
        from pyweber.pyweber.pyweber import Pyweber
        from pyweber.utils.security import CSRF_COOKIE_NAME, CSRF_FORM_FIELD, generate_csrf_token

        app = Pyweber()

        @app.route('/login', methods=['POST'])
        def login():
            return 'ok'

        token = generate_csrf_token()
        body = f'{CSRF_FORM_FIELD}={token}&user=x'.encode()
        headers = (
            'POST /login HTTP/1.1\r\n'
            'Host: localhost\r\n'
            'Content-Type: application/x-www-form-urlencoded; charset=UTF-8\r\n'
            f'Cookie: {CSRF_COOKIE_NAME}={token}\r\n'
            f'Content-Length: {len(body)}\r\n\r\n'
        )
        resp = await app.get_response(Request(headers=headers, body=body))
        assert resp.status_code == 200
        assert b'ok' in resp.response_content
