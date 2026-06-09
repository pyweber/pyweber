import pytest
from unittest.mock import Mock, patch, AsyncMock

from pyweber.models.middleware import MiddlewareManager, MiddlewareResult
from pyweber.models.request import Request
from pyweber.models.response import Response
from pyweber.core.template import Template


WSGI = 'GET / HTTP/1.1\r\nHost: localhost\r\n\r\n'


class TestMiddlewareManager:
    @pytest.fixture
    def manager(self):
        return MiddlewareManager()

    @pytest.fixture
    def http_request(self):
        return Request(headers=WSGI, body=b'')

    def test_before_request_decorator(self, manager):
        @manager.before_request()
        def auth(req: Request):
            return None

        assert len(manager.get_before_request_middlewares) == 1

    def test_after_request_decorator(self, manager):
        @manager.after_request()
        def add_header(resp: Response):
            return resp

        assert len(manager.get_after_request_middlewares) == 1

    @pytest.mark.asyncio
    async def test_before_request_short_circuit(self, manager, http_request):
        @manager.before_request(status_code=401, process_response=True)
        def block(req: Request):
            return Template(template='blocked')

        result = await manager.process_middleware(
            resp=http_request,
            middlewares=manager.get_before_request_middlewares,
        )
        assert isinstance(result, MiddlewareResult)
        assert result.status_code == 401

    def test_clear_middlewares(self, manager):
        @manager.before_request()
        def a(req: Request):
            return None

        manager.clear_before_request_middleware()
        assert manager.get_before_request_middlewares == []

    def test_invalid_middleware_signature_raises(self, manager):
        with pytest.raises(TypeError):
            manager.set_middleware(
                status_code=200,
                middleware=lambda req, extra: None,
            )
