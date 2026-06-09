import base64
import hashlib

import pytest

from pyweber.connection.websocket import WebsocketUpgrade, need_message_keys


class TestNeedMessageKeys:
    def test_returns_required_keys(self):
        keys = need_message_keys()
        assert 'sessionId' in keys
        assert 'route' in keys
        assert 'type' in keys


class TestWebsocketUpgrade:
    @pytest.fixture
    def upgrade_headers(self):
        key = base64.b64encode(b'test-websocket-key!!').decode()
        headers = (
            f'GET / HTTP/1.1\r\n'
            f'Host: localhost\r\n'
            f'Connection: Upgrade\r\n'
            f'Upgrade: websocket\r\n'
            f'Sec-WebSocket-Key: {key}\r\n\r\n'
        ).encode('iso-8859-1')
        return WebsocketUpgrade(headers=headers)

    def test_client_secret_key_extracted(self, upgrade_headers):
        assert upgrade_headers.client_secret_key is not None

    def test_server_accept_key_matches_rfc(self, upgrade_headers):
        guid = '258EAFA5-E914-47DA-95CA-C5AB0DC85B11'
        expected = base64.b64encode(
            hashlib.sha1(
                (upgrade_headers.client_secret_key + guid).encode('utf-8')
            ).digest()
        ).decode('utf-8')
        assert upgrade_headers.server_accept_key == expected

    def test_upgrade_response_contains_101(self, upgrade_headers):
        response = upgrade_headers.upgrade_response
        assert '101 Switching Protocols' in response
        assert 'Sec-WebSocket-Accept' in response
