import pytest

from pyweber.models.routes import Route, RouteManager, RouteNotFoundError
from pyweber.utils.types import ContentTypes


class RouteManagerStub(RouteManager):
    """RouteManager mínimo para testar APIs sem Pyweber completo."""

    def __init__(self):
        RouteManager.__init__(self)


class TestRoutesApi:
    def setup_method(self):
        self.rm = RouteManagerStub()

    def test_add_route_and_resolve(self):
        self.rm.add_route(route='/items/{id}', template='item', methods=['GET'])
        path, kw = self.rm.resolve_path('/items/42')
        assert path == '/items/{id}'
        assert kw.get('id') == '42'

    def test_route_decorator(self):
        @self.rm.route('/decorated', methods=['GET'], name='deco')
        def handler(request, **kwargs):
            return 'ok'

        assert self.rm.exists(route='/decorated')
        assert self.rm.get_route_by_name('deco') is not None

    def test_redirect_and_build(self):
        self.rm.add_route(route='/new', template='n', methods=['GET'], name='new')
        self.rm.redirect(from_route='/old', target='new')
        assert self.rm.is_redirected('/old')

    def test_duplicate_route_raises(self):
        self.rm.add_route(route='/dup', template='a', methods=['GET'])
        from pyweber.utils.exceptions import RouteAlreadyExistError
        with pytest.raises(RouteAlreadyExistError):
            self.rm.add_route(route='/dup', template='b', methods=['GET'])

    def test_redirect_unknown_target(self):
        with pytest.raises(RouteNotFoundError):
            self.rm.redirect(from_route='/x', target='/missing')

    def test_route_object(self):
        route = Route(
            route='/x',
            template='t',
            methods=['GET'],
            content_type=ContentTypes.html,
            group=Route.default_group(),
        )
        assert route.full_route == '/x'
        assert 'GET' in route.methods
