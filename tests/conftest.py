import pytest

from pyweber.pyweber.pyweber import Pyweber
from pyweber.core.template import Template
from pyweber.utils.types import ContentTypes
from pyweber.connection.websocket import WebsocketManager


@pytest.fixture
def pyweber_app():
    app = Pyweber()
    ws = WebsocketManager(app=app, protocol='pyweber')
    app.ws_server = ws
    app.add_route(
        route='/',
        template=Template(template='<html><body>Hello</body></html>'),
        methods=['GET'],
    )
    app.add_route(
        route='/api/echo',
        template=lambda request, **kwargs: {'ok': True},
        methods=['POST'],
        content_type=ContentTypes.json,
    )
    return app


@pytest.fixture
def http_server(pyweber_app):
    from pyweber.connection.http import HttpServer

    server = HttpServer()
    server.timeout = 2
    server.app = pyweber_app
    yield server
    shutdown = getattr(server._pool, 'shutdown', None)
    if shutdown:
        shutdown(wait=False, cancel_futures=True)
