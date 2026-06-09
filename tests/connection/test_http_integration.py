import asyncio
import socket

import pytest

from helpers import RecvSocket, make_http_request, make_ws_upgrade_request


class TestProcessRequest:
    @pytest.mark.asyncio
    async def test_reads_headers_and_body(self, http_server):
        body = b'{"name":"test"}'
        raw = make_http_request('POST', '/api/echo', body, 'Content-Type: application/json\r\n')
        client = RecvSocket(raw)

        headers, received_body = await http_server.process_request(client)
        assert b'POST /api/echo' in headers
        assert received_body == body

    @pytest.mark.asyncio
    async def test_empty_request_on_timeout(self, http_server):
        async def fail_read(*args, **kwargs):
            raise asyncio.TimeoutError

        http_server.read_data = fail_read
        headers, body = await http_server.process_request(RecvSocket(b''))
        assert headers == b''
        assert body == b''


class TestPeekAndDispatch:
    def test_peek_detects_websocket(self, http_server):
        client = RecvSocket(make_ws_upgrade_request())
        is_ws, raw = http_server._peek_is_websocket(client)
        assert is_ws is True
        assert b'Upgrade' in raw

    def test_peek_detects_http(self, http_server):
        client = RecvSocket(make_http_request())
        is_ws, raw = http_server._peek_is_websocket(client)
        assert is_ws is False
        assert b'GET /' in raw

    def test_dispatch_http_submits_to_pool(self, http_server, monkeypatch):
        submitted = []

        class Pool:
            def submit(self, fn, coro):
                submitted.append(coro)
                coro.close()

        http_server._pool = Pool()
        client = RecvSocket(make_http_request())
        http_server._dispatch_client(client)
        assert len(submitted) == 1


class TestHandleHttpRaw:
    @pytest.mark.asyncio
    async def test_returns_response_bytes(self, http_server, monkeypatch):
        from pyweber.models.response import Response
        from pyweber.utils.types import ContentTypes

        raw = make_http_request('GET', '/')
        client = RecvSocket(raw)

        async def fake_get_response(request):
            return Response(
                request=request,
                response_content=b'Hello',
                code=200,
                cookies={},
                response_type=ContentTypes.html,
                route='/',
            )

        monkeypatch.setattr(http_server.app, 'get_response', fake_get_response)
        await http_server._handle_http_raw(client, raw)
        assert client.closed is True
        assert b'HTTP/1.1' in client.sent
        assert b'Hello' in client.sent



class TestHttpServerUtils:
    def test_get_local_ip(self, http_server):
        ip = http_server.get_local_ip()
        assert ip.count('.') == 3

    def test_get_local_ip_offline_fallback(self, http_server, monkeypatch):
        real_socket = socket.socket

        class OfflineSocket(real_socket):
            def connect(self, address):
                if address[0] == '8.8.8.8':
                    raise OSError('Network unreachable')
                return super().connect(address)

        monkeypatch.setattr(socket, 'socket', OfflineSocket)
        ip = http_server.get_local_ip()
        assert ip.count('.') == 3

    def test_clear_cache_removes_pycache(self, http_server, tmp_path):
        cache = tmp_path / '__pycache__'
        cache.mkdir()
        (cache / 'mod.pyc').write_bytes(b'x')
        http_server.clear_cache(path=str(tmp_path))
        assert not cache.exists()
