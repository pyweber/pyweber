import asyncio
import ssl
from unittest.mock import MagicMock, patch

import pytest

from pyweber.connection.http import HttpServer
from helpers import RecvSocket, make_http_request


class TestHttpServerExtended:
    @pytest.fixture
    def server(self, pyweber_app):
        s = HttpServer()
        s.app = pyweber_app
        s.timeout = 1
        return s

    def test_setup_ssl(self, server, tmp_path):
        cert = tmp_path / 'cert.pem'
        key = tmp_path / 'key.pem'
        cert.write_text('cert')
        key.write_text('key')
        with patch('ssl.create_default_context') as mock_ctx:
            mock_ctx.return_value.load_cert_chain = MagicMock()
            server.setup_ssl(str(cert), str(key))
        assert server.ssl_context is not None

    @pytest.mark.asyncio
    async def test_read_data(self, server):
        data = await server.read_data(RecvSocket(b'abc'), 3)
        assert data == b'abc'

    def test_generate_qrcode(self, server, capsys):
        with patch('qrcode.QRCode') as mock_qr_cls:
            qr = MagicMock()
            mock_qr_cls.return_value = qr
            server.generate_qrcode('http://localhost:8800')
            qr.add_data.assert_called_once()
            qr.print_ascii.assert_called_once()

    def test_dispatch_websocket_uses_thread(self, server, monkeypatch):
        from helpers import make_ws_upgrade_request

        started = []

        class FakeThread:
            def __init__(self, target=None, args=(), daemon=False):
                started.append(True)

            def start(self):
                pass

        monkeypatch.setattr('pyweber.connection.http.threading.Thread', FakeThread)
        client = RecvSocket(make_ws_upgrade_request())
        server._dispatch_client(client)
        assert started
