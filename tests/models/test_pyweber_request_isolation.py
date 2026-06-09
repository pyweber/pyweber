import pytest

from pyweber.pyweber.pyweber import Pyweber
from pyweber.models.request import Request, ClientInfo


WSGI = 'GET / HTTP/1.1\r\nHost: localhost\r\n\r\n'


class TestPyweberGetResponseIsolation:
    @pytest.mark.asyncio
    async def test_cookies_cleared_after_response(self):
        app = Pyweber()

        def handler(request, **kwargs):
            app.set_cookie('token', 'abc')
            return 'ok'

        app.add_route(route='/', template=handler, methods=['GET'])
        req = Request(
            headers=WSGI,
            body=b'',
            client_info=ClientInfo(host='127.0.0.1', port=1),
        )

        resp = await app.get_response(req)
        assert resp.headers['Set-Cookie']['token'].startswith('token=abc')
        assert app.cookies == {}

    @pytest.mark.asyncio
    async def test_sequential_requests_keep_isolated_cookies(self):
        app = Pyweber()
        state = {'call': 0}

        def handler(request, **kwargs):
            state['call'] += 1
            if state['call'] == 1:
                app.set_cookie('user', 'joao')
            else:
                app.set_cookie('user', 'maria')
            return str(state['call'])

        app.add_route(route='/', template=handler, methods=['GET'])
        req = Request(
            headers=WSGI,
            body=b'',
            client_info=ClientInfo(host='127.0.0.1', port=1),
        )

        resp_a = await app.get_response(req)
        resp_b = await app.get_response(req)

        assert resp_a.headers['Set-Cookie']['user'].startswith('user=joao')
        assert resp_b.headers['Set-Cookie']['user'].startswith('user=maria')
