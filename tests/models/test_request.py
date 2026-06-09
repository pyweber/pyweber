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
