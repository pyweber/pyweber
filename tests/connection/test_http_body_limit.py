"""HTTP body size limit tests."""

from __future__ import annotations

import asyncio
from unittest.mock import MagicMock, AsyncMock, patch

import pytest

from pyweber.connection.http import HttpServer


class TestBodySizeLimit:
    @pytest.mark.asyncio
    async def test_process_request_rejects_oversized_content_length(self, monkeypatch):
        monkeypatch.setenv('PYWEBER_MAX_BODY_SIZE', '100')
        server = HttpServer()
        server.timeout = 1

        headers = (
            b'POST / HTTP/1.1\r\n'
            b'Host: localhost\r\n'
            b'Content-Length: 500\r\n'
            b'\r\n'
        )

        class FakeClient:
            def __init__(self):
                self.sent = []
                self._chunks = [headers]

            def recv(self, n):
                if self._chunks:
                    return self._chunks.pop(0)
                return b''

            def sendall(self, data):
                self.sent.append(data)

            def getpeername(self):
                return ('127.0.0.1', 12345)

            def close(self):
                pass

        client = FakeClient()

        async def read_data(c, length):
            return c.recv(length)

        server.read_data = read_data
        result = await server.process_request(client)
        assert result == (None, None)
        assert any(b'413' in chunk for chunk in client.sent)


class TestHttpParseAndProcess:
    @pytest.fixture
    def server(self, pyweber_app):
        s = HttpServer()
        s.app = pyweber_app
        s.timeout = 2
        return s

    def test_parse_cookies_empty(self, server):
        assert server._parse_cookies('GET / HTTP/1.1\r\nHost: x\r\n\r\n') == {}

    def test_parse_cookies_multiple(self, server):
        headers = (
            'GET / HTTP/1.1\r\n'
            'Host: localhost\r\n'
            'Cookie: a=1; b=two; bare; c=3\r\n'
            '\r\n'
        )
        cookies = server._parse_cookies(headers)
        assert cookies['a'] == '1'
        assert cookies['b'] == 'two'
        assert cookies['c'] == '3'
        assert 'bare' not in cookies

    @pytest.mark.asyncio
    async def test_send_simple_error(self, server):
        from helpers import RecvSocket

        client = RecvSocket(b'')
        await server._send_simple_error(client, 400, b'Bad Request')
        assert b'400' in client.sent
        assert b'Bad Request' in client.sent
        assert b'Content-Length:' in client.sent

    @pytest.mark.asyncio
    async def test_process_request_happy_path_with_body(self, server):
        from helpers import RecvSocket, make_http_request

        body = b'hello=world'
        raw = make_http_request('POST', '/api/echo', body=body)
        client = RecvSocket(raw)
        headers, got_body = await server.process_request(client)
        assert headers.startswith(b'POST /api/echo')
        assert got_body == body

    @pytest.mark.asyncio
    async def test_process_request_get_no_body(self, server):
        from helpers import RecvSocket, make_http_request

        raw = make_http_request('GET', '/')
        client = RecvSocket(raw)
        headers, got_body = await server.process_request(client)
        assert headers.startswith(b'GET /')
        assert got_body == b''

    @pytest.mark.asyncio
    async def test_handle_http_happy_path(self, server):
        from helpers import RecvSocket, make_http_request

        raw = make_http_request('GET', '/')
        client = RecvSocket(raw)
        await server.handle_http(client)
        assert client.closed
        assert b'200' in client.sent or b'HTTP/1.1' in client.sent

    @pytest.mark.asyncio
    async def test_handle_http_raw_small_body(self, server):
        from helpers import RecvSocket, make_http_request

        body = b'{"x":1}'
        raw = make_http_request('POST', '/api/echo', body=body, extra_headers='Content-Type: application/json\r\n')
        client = RecvSocket(b'')
        await server._handle_http_raw(client, raw)
        assert client.closed
        assert client.sent  # response written
