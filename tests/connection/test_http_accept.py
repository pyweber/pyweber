import socket
import threading
from unittest.mock import Mock, patch

import pytest

from pyweber.connection.http import HttpServer


@pytest.fixture
def http_server():
    server = HttpServer()
    server.host = '127.0.0.1'
    server.port = 0
    server.timeout = 1
    server.ssl_context = None
    server._dispatch_client = Mock()
    return server


class TestAcceptClients:
    def test_drains_multiple_connections(self, http_server):
        listen = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        listen.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        listen.bind(('127.0.0.1', 0))
        listen.listen(socket.SOMAXCONN)
        listen.setblocking(False)
        port = listen.getsockname()[1]

        clients = []
        for _ in range(3):
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect(('127.0.0.1', port))
            clients.append(client)

        http_server._accept_clients(listen)
        assert http_server._dispatch_client.call_count == 3

        for client in clients:
            client.close()
        listen.close()

    def test_stops_on_empty_queue(self, http_server):
        listen = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        listen.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        listen.bind(('127.0.0.1', 0))
        listen.listen(1)
        listen.setblocking(False)

        http_server._accept_clients(listen)
        http_server._dispatch_client.assert_not_called()
        listen.close()
