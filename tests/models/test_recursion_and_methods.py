import pytest

from pyweber.pyweber.pyweber import Pyweber
from pyweber.models.request import Request, ClientInfo
from pyweber.models.routes import RedirectRoute
from pyweber.utils.exceptions import RouteAlreadyExistError


def _request(method: str, path: str) -> Request:
    return Request(
        headers=f'{method} {path} HTTP/1.1\r\nHost: localhost\r\n\r\n',
        body=b'',
        client_info=ClientInfo(host='127.0.0.1', port=1),
    )


class TestRouteVisitTracking:
    @pytest.mark.asyncio
    async def test_sequential_requests_do_not_false_recursion(self):
        app = Pyweber()
        app.add_route(route='/items', template=lambda **kw: 'ok', methods=['GET'])
        req = _request('GET', '/items')

        first = await app.get_response(req)
        second = await app.get_response(req)

        assert first.status_code == 200
        assert second.status_code == 200

    @pytest.mark.asyncio
    async def test_sequential_redirect_requests_do_not_false_recursion(self):
        app = Pyweber()
        app.add_route(route='/target', template='final', methods=['GET'], name='target')
        app.redirect(from_route='/entry', target='target')
        req = _request('GET', '/entry')

        first = await app.get_response(req)
        second = await app.get_response(req)

        assert first.status_code == 302
        assert second.status_code == 302

    @pytest.mark.asyncio
    async def test_redirect_loop_raises_recursion_error(self):
        app = Pyweber()
        app.add_route(route='/a', template='x', methods=['GET'])
        app.add_route(route='/b', template='x', methods=['GET'])
        app.update_route('/a', template=lambda **kw: RedirectRoute(route=app.get_route_by_path('/b')))
        app.update_route('/b', template=lambda **kw: RedirectRoute(route=app.get_route_by_path('/a')))

        resp = await app.get_response(_request('GET', '/a'))

        assert resp.status_code == 500


class TestMultiMethodRoutes:
    @pytest.mark.asyncio
    async def test_disallowed_method_returns_405_with_allow_header(self):
        app = Pyweber()
        app.add_route(
            route='/resource',
            template=lambda request, **kw: f'{request.method}',
            methods=['GET', 'POST'],
        )

        resp = await app.get_response(_request('DELETE', '/resource'))

        assert resp.status_code == 405
        assert resp.headers['Allow'] == 'GET, POST'
        assert b'405 Method Not Allowed' in resp.response_content

    @pytest.mark.asyncio
    async def test_allowed_methods_still_work(self):
        app = Pyweber()
        app.add_route(
            route='/resource',
            template=lambda request, **kw: request.method,
            methods=['GET', 'POST'],
        )

        get_resp = await app.get_response(_request('GET', '/resource'))
        post_resp = await app.get_response(_request('POST', '/resource'))

        assert get_resp.status_code == 200
        assert post_resp.status_code == 200

    @pytest.mark.asyncio
    async def test_update_route_can_add_delete_method(self):
        app = Pyweber()
        app.add_route(route='/resource', template='x', methods=['GET', 'POST'])
        app.update_route('/resource', methods=['GET', 'POST', 'DELETE'])

        resp = await app.get_response(_request('DELETE', '/resource'))

        assert resp.status_code == 200

    def test_cannot_register_duplicate_path_for_different_methods(self):
        app = Pyweber()
        app.add_route(route='/resource', template='a', methods=['GET', 'POST'])

        with pytest.raises(RouteAlreadyExistError):
            app.add_route(route='/resource', template='b', methods=['DELETE'])
