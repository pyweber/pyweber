import asyncio
import json

import pytest

from helpers import RecvSocket, make_masked_frame
from pyweber.connection.websocket import WebsocketServer, WebsocketManager, event_is_running
from pyweber.pyweber.pyweber import Pyweber
from pyweber.core.template import Template


class TestWebsocketFrames:
    @pytest.mark.asyncio
    async def test_frame_to_send_text(self):
        ws = WebsocketServer(RecvSocket(b''))
        frame = await ws.frame_to_send(b'hello', opcode=1)
        assert frame[0] & 0x0F == 1
        assert frame[0] & 0x80
        assert b'hello' in frame

    @pytest.mark.asyncio
    async def test_frame_to_send_large_payload(self):
        ws = WebsocketServer(RecvSocket(b''))
        payload = b'x' * 200
        frame = await ws.frame_to_send(payload, opcode=2)
        assert frame[1] == 126

    @pytest.mark.asyncio
    async def test_receive_text_frame(self):
        payload = b'{"ping":true}'
        sock = RecvSocket(make_masked_frame(payload))
        ws = WebsocketServer(sock)
        opcode, message, fin = await ws.receive_frame()
        assert opcode == 1
        assert message == payload
        assert fin == 1

    @pytest.mark.asyncio
    async def test_receive_rejects_unmasked_client_frame(self):
        # Frame sem bit de mask — servidor deve ignorar
        raw = bytes([0x81, 5]) + b'hello'
        ws = WebsocketServer(RecvSocket(raw))
        opcode, message, fin = await ws.receive_frame()
        assert opcode is None


class TestWebsocketServerMore:
    @pytest.mark.asyncio
    async def test_frame_to_send_huge_payload(self):
        ws = WebsocketServer(RecvSocket(b''))
        payload = b'y' * 70000
        frame = await ws.frame_to_send(payload, opcode=2)
        assert frame[1] == 127

    @pytest.mark.asyncio
    async def test_frame_to_send_invalid_utf8_switches_opcode(self):
        ws = WebsocketServer(RecvSocket(b''))
        frame = await ws.frame_to_send(b'\xff\xfe', opcode=1)
        assert frame[0] & 0x0F == 2

    @pytest.mark.asyncio
    async def test_send_and_close(self):
        sock = RecvSocket(b'')
        ws = WebsocketServer(sock)
        await ws.send(b'hi', opcode=1)
        assert sock.sent
        await ws.close()
        assert sock.closed

    @pytest.mark.asyncio
    async def test_read_exact_zero(self):
        ws = WebsocketServer(RecvSocket(b''))
        assert await ws.read_exact(0) == b''

    @pytest.mark.asyncio
    async def test_receive_extended_126(self):
        payload = b'z' * 200
        sock = RecvSocket(make_masked_frame(payload))
        ws = WebsocketServer(sock)
        opcode, message, fin = await ws.receive_frame()
        assert opcode == 1
        assert message == payload

    def test_iter_next_empty_raises(self):
        ws = WebsocketServer(RecvSocket(b''))
        with pytest.raises(StopIteration):
            next(ws)

    def test_iter_with_queued_message(self):
        ws = WebsocketServer(RecvSocket(b''))
        ws._WebsocketServer__messages.append(b'queued')
        assert next(iter(ws)) == b'queued'

    @pytest.mark.asyncio
    async def test_aiter_yields_queued(self):
        ws = WebsocketServer(RecvSocket(b''))
        ws._WebsocketServer__messages.append('hello')

        async def take_one():
            async for msg in ws:
                return msg

        result = await asyncio.wait_for(take_one(), timeout=1)
        assert result == 'hello'


class TestWebsocketManager:
    @pytest.fixture
    def manager(self, pyweber_app):
        return pyweber_app.ws_server

    def test_process_ws_message_rejects_incomplete(self, manager):
        assert manager.process_ws_message_handler('not-json') == {}
        assert manager.process_ws_message_handler(json.dumps({'foo': 'bar'})) == {}

    def test_process_ws_message_valid_minimal(self, manager):
        message = {
            'type': '',
            'event_ref': '',
            'route': '/',
            'target_uuid': '',
            'current_target_uuid': '',
            'template': '<html></html>',
            'values': {},
            'event_data': {},
            'window_data': {'width': 100},
            'window_response': {},
            'window_event': '',
            'sessionId': 'sess-test',
            'file_content': {},
        }
        result = manager.process_ws_message_handler(json.dumps(message))
        assert result.get('route') == '/'

    def test_add_session(self, manager):
        from pyweber.core.window import Window
        from pyweber.connection.session import sessions

        template = Template(template='<html></html>')
        manager.add_session(
            session_id='sess-x',
            template=template,
            window=Window(),
            route='/',
        )
        assert sessions.get_session('sess-x') is not None
        assert sessions.get_session('sess-x').current_route == '/'
        sessions.remove_session('sess-x')

    @pytest.mark.asyncio
    async def test_set_window_response_resolves_future(self, manager):
        async def waiter():
            return await manager.get_window_response(timeout=1, session_id='s1')

        task = asyncio.create_task(waiter())
        await asyncio.sleep(0.05)
        await manager.set_window_response({'confirm_result': 'yes'}, session_id='s1')
        result = await task
        assert result == {'confirm_result': 'yes'}

    @pytest.mark.asyncio
    async def test_send_message_pyweber_protocol(self, manager):
        sent = []

        class FakeConn:
            async def send(self, data, opcode=1):
                sent.append(data)

        manager.ws_connections['sess-1'] = FakeConn()
        from pyweber.connection.session import Session
        from pyweber.core.window import Window

        template = Template(template='<html><head></head><body></body></html>')
        manager.add_session('sess-1', template, Window(), '/')

        await manager.send_message(data={'reload': True}, session_id='sess-1')
        assert len(sent) == 1
        assert b'reload' in sent[0]
