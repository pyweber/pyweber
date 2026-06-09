import pytest

from pyweber.pyweber.pyweber import Pyweber
from pyweber.core.template import Template
from pyweber.models.routes import RedirectRoute, Route
from pyweber.utils.types import ContentTypes


@pytest.fixture
def app():
    p = Pyweber()
    p.add_route(route='/hello', template=lambda request, **kw: 'hello', methods=['GET'])
    p.add_route(route='/json', template={'ok': True}, methods=['GET'], content_type=ContentTypes.json)
    p.add_route(route='/page', template=Template(template='<body>Page</body>'), methods=['GET'])
    return p


class TestRouteManagerExtended:
    def test_list_routes_and_exists(self, app):
        assert app.exists(route='/hello')
        assert '/hello' in app.list_routes

    def test_get_route_by_name_and_group(self, app):
        app.add_route(route='/named', template='x', methods=['GET'], name='named-route')
        assert app.get_route_by_name(name='named-route') is not None

    def test_redirect_route(self, app):
        app.add_route(route='/target', template='target', methods=['GET'], name='target')
        app.redirect(from_route='/old', target='target')
        assert app.is_redirected(route='/old')

    def test_static_directory(self, app, tmp_path, monkeypatch):
        static = tmp_path / 'assets'
        static.mkdir()
        (static / 'app.txt').write_text('static-content')
        monkeypatch.chdir(tmp_path)
        app.static('assets')
        assert app.is_static_file(route='/assets/app.txt')

    def test_build_route_with_params(self, app):
        app.add_route(route='/users/{user_id}', template='u', methods=['GET'])
        built = app.build_route('/users/{user_id}', user_id='42')
        assert '42' in built

    def test_normaize_path(self, app):
        assert app.normaize_path('/foo/bar') == 'foo\\bar' or 'foo/bar' in app.normaize_path('/foo/bar')

    def test_clear_cache_templates(self, app):
        app.clear_cache_templates()
        assert app._Pyweber__cache_templates == {}


class TestPyweberUtilities:
    def test_events_decorator(self, app):
        from pyweber.utils.types import WindowEventType

        @app.events(WindowEventType.LOAD, route='/hello')
        def on_load(e):
            return e

        assert callable(on_load)

    def test_template_to_bytes_variants(self, app):
        result = app.template_to_bytes(template={'a': 1}, content_type=ContentTypes.json)
        assert result.content_type == ContentTypes.json
        result2 = app.template_to_bytes(template=b'raw', content_type=ContentTypes.txt)
        assert result2.content == b'raw'
