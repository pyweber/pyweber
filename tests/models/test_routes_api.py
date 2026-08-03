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

    def test_same_path_different_methods_allowed(self):
        self.rm.add_route(route='/api', template='get', methods=['GET'], name='api-get')
        self.rm.add_route(route='/api', template='post', methods=['POST'], name='api-post')

        assert self.rm.exists('/api')
        assert set(self.rm.get_allowed_methods('/api')) == {'GET', 'POST'}
        assert self.rm.get_route_by_path('/api', method='GET') is not None
        assert self.rm.get_route_by_path('/api', method='POST') is not None
        assert self.rm.get_route_by_name('api-get') is not None
        assert self.rm.get_route_by_name('api-post') is not None
        assert len(self.rm.get_routes_by_path('/api')) == 2

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

    def test_static_resolve_exact(self):
        self.rm.add_route(route='/hello', template='h', methods=['GET'])
        self.rm.add_route(route='/users/{id}', template='u', methods=['GET'])
        path, kw = self.rm.resolve_path('/hello')
        assert path == '/hello'
        assert kw == {}

    def test_static_wins_over_dynamic_param(self):
        """Exact static paths take precedence over ``{param}`` patterns."""
        self.rm.add_route(route='/users/{id}', template='dyn', methods=['GET'])
        self.rm.add_route(route='/users/me', template='me', methods=['GET'])
        path, kw = self.rm.resolve_path('/users/me')
        assert path == '/users/me'
        assert 'id' not in kw

    def test_dynamic_first_match_order(self):
        self.rm.add_route(route='/a/{x}/b', template='1', methods=['GET'])
        self.rm.add_route(route='/a/{y}/b', template='2', methods=['GET'])
        path, kw = self.rm.resolve_path('/a/1/b')
        assert path == '/a/{x}/b'
        assert kw.get('x') == '1'

    def test_multi_segment_params(self):
        self.rm.add_route(route='/org/{org}/team/{team}', template='t', methods=['GET'])
        path, kw = self.rm.resolve_path('/org/acme/team/ops')
        assert path == '/org/{org}/team/{team}'
        assert kw == {'org': 'acme', 'team': 'ops'}

    def test_group_routes_resolve(self):
        routes = [
            Route(route='/ping', template='p', methods=['GET'], group='api'),
            Route(route='/items/{id}', template='i', methods=['GET'], group='api'),
        ]
        self.rm.add_group_routes(routes, group='api')
        assert self.rm.exists('/api/ping')
        path, kw = self.rm.resolve_path('/api/items/9')
        assert path == '/api/items/{id}'
        assert kw.get('id') == '9'

    def test_query_params_merged(self):
        self.rm.add_route(route='/search/{q}', template='s', methods=['GET'])
        path, kw = self.rm.resolve_path('/search/foo?page=2&sort=asc')
        assert path == '/search/{q}'
        assert kw.get('q') == 'foo'
        assert kw.get('page') == '2'
        assert kw.get('sort') == 'asc'

    def test_remove_dynamic_unindexes(self):
        self.rm.add_route(route='/items/{id}', template='i', methods=['GET'])
        assert self.rm.exists('/items/1')
        self.rm.remove_route(route='/items/{id}')
        path, kw = self.rm.resolve_path('/items/1')
        assert path == '/items/1'
        assert 'id' not in kw
