import pytest

from pyweber.pyweber.pyweber import Pyweber
from pyweber.core.template import Template
from pyweber.models.request import Request, ClientInfo
from pyweber.utils.types import ContentTypes


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
