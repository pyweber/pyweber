import pytest

from pyweber.pyweber.pyweber import Pyweber
from pyweber.models.context import get_current_request, reset_current_request, set_current_request
from pyweber.models.request import Request, ClientInfo


WSGI = 'GET /login HTTP/1.1\r\nHost: localhost\r\n\r\n'


class TestGetTemplateRequestContext:
    @pytest.mark.asyncio
    async def test_get_template_without_http_uses_stub_request(self):
        app = Pyweber()
        seen = {}

        @app.route('/login')
        def unified_login(request: Request):
            seen['method'] = request.method
            seen['path'] = request.path
            return '<html>login</html>'

        assert get_current_request() is None

        result = await app.get_template(route='/login', method='GET')
        assert 'login' in str(result.template)
        assert seen['method'] == 'GET'
        assert seen['path'] == '/login'
        assert get_current_request() is None

    @pytest.mark.asyncio
    async def test_clone_template_provides_request_to_handler(self):
        app = Pyweber()

        @app.route('/login')
        def unified_login(request: Request):
            if request.method.upper() == 'POST':
                return '<html>post</html>'
            return '<html>get</html>'

        clone = await app.clone_template(route='/login')
        assert 'get' in clone.build_html().lower()

    @pytest.mark.asyncio
    async def test_get_response_still_sets_request_context(self):
        app = Pyweber()
        app.add_route(route='/', template=lambda: 'ok', methods=['GET'])

        req = Request(
            headers=WSGI.replace('/login', '/'),
            body=b'',
            client_info=ClientInfo(host='127.0.0.1', port=1),
        )

        await app.get_response(req)
        assert get_current_request() is None
        assert app.request is None
