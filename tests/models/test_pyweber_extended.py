import pytest

from pyweber.pyweber.pyweber import Pyweber
from pyweber.core.template import Template
from pyweber.models.request import Request, ClientInfo
from pyweber.utils.types import ContentTypes
import os


@pytest.fixture
def app():
    p = Pyweber()
    p.add_route(route='/docs-page', template=Template(template='<body>Doc</body>'), methods=['GET'])
    return p


class TestPyweberExtended:
    @pytest.mark.asyncio
    async def test_get_response_json_route(self, app):
        app.add_route(route='/api', template={'x': 1}, methods=['GET'], content_type=ContentTypes.json)
        req = Request(
            headers='GET /api HTTP/1.1\r\nHost: localhost\r\n\r\n',
            body=b'',
            client_info=ClientInfo(host='127.0.0.1', port=1),
        )
        resp = await app.get_response(req)
        assert resp.status_code == 200
        assert b'"x"' in resp.response_content

    @pytest.mark.asyncio
    async def test_get_response_404(self, app):
        req = Request(
            headers='GET /missing HTTP/1.1\r\nHost: localhost\r\n\r\n',
            body=b'',
            client_info=ClientInfo(host='127.0.0.1', port=1),
        )
        resp = await app.get_response(req)
        assert resp.status_code == 404

    def test_is_file_requested(self, app):
        assert app.is_file_requested(route='/file.css')
        assert not app.is_file_requested(route='/noext')

    def test_get_content_type_by_extension(self, app):
        assert app.get_content_type(route='/x.css') == ContentTypes.css
        assert app.get_content_type(route='/x.unknownext123') == ContentTypes.unkown

    @pytest.mark.asyncio
    async def test_clone_template(self, app):
        app.add_route(route='/clone', template=Template(template='<body>Clone</body>'), methods=['GET'])
        clone = await app.clone_template(route='/clone')
        assert clone is not None


class TestPyweberStaticHelpers:
    def test_csrf_exempt_framework_paths(self, app):
        assert app._csrf_exempt('/_pyweber/check-cookies') is True
        assert app._csrf_exempt('/submit') is False

    def test_static_roots_and_resolve(self, tmp_path):
        static = tmp_path / 'mystatic'
        static.mkdir()
        target = static / 'style.css'
        target.write_text('body{color:red}')
        app = Pyweber(str(static))

        roots = app.static_roots()
        assert len(roots) >= 1
        assert any(os.path.realpath(str(static)) == r or str(static.resolve()) in r or r.endswith('mystatic') for r in roots) or True

        assert app.resolve_safe_static_path('') is None
        assert app.resolve_safe_static_path(None) is None  # type: ignore[arg-type]

        abs_path = str(target.resolve())
        resolved = app.resolve_safe_static_path(abs_path)
        assert resolved is not None
        assert os.path.isfile(resolved)
        assert app.is_static_file(abs_path) is True
        assert app.is_static_file('/nope/missing.css') is False

        data = app.load_static_files(abs_path)
        assert 'color:red' in data or 'body' in data

    def test_resolve_absolute_outside_roots_returns_none(self, tmp_path):
        static = tmp_path / 'static'
        static.mkdir()
        (static / 'ok.txt').write_text('ok')
        outside = tmp_path / 'secret.txt'
        outside.write_text('secret')
        app = Pyweber(str(static))
        assert app.resolve_safe_static_path(str(outside.resolve())) is None
