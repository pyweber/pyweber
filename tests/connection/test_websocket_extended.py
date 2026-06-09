import asyncio
import json

import pytest

from pyweber.connection.websocket import WebsocketManager
from pyweber.core.template import Template
from pyweber.core.window import Window
from pyweber.connection.session import sessions, Session


class TestWebsocketManagerExtended:
    @pytest.fixture
    def manager(self, pyweber_app):
        return pyweber_app.ws_server

    @pytest.mark.asyncio
    async def test_get_file_content_timeout(self, manager):
        result = await manager.get_file_content(timeout=0.01, file_id='missing')
        assert result is None

    @pytest.mark.asyncio
    async def test_set_and_get_file_content(self, manager):
        async def waiter():
            return await manager.get_file_content(timeout=1, file_id='f1')

        task = asyncio.create_task(waiter())
        await asyncio.sleep(0.05)
        await manager.set_file_content({'data': b'chunk'}, file_id='f1')
        assert await task == {'data': b'chunk'}

    @pytest.mark.asyncio
    async def test_data_to_json_with_template(self, manager):
        template = Template(template='<html><body></body></html>')
        manager.add_session('s-json', template, Window(), '/')
        data = {'template': template}
        result = await manager.data_to_json(data, session_id='s-json')
        parsed = json.loads(result)
        assert 'template' in parsed
        sessions.remove_session('s-json')

    def test_remove_connection_and_get(self, manager):
        from helpers import RecvSocket
        from pyweber.connection.websocket import WebsocketServer

        conn = WebsocketServer(RecvSocket(b''))
        conn.id = 'conn-1'
        manager.add_connection(conn)
        assert manager.get_connection('conn-1') is conn
        manager.remove_connection('conn-1')
        assert manager.get_connection('conn-1') is None

    def test_get_session_id_generates_uuid(self, manager):
        sid = manager.get_session_id()
        assert sid
        assert manager.get_session_id(session_id='fixed') == 'fixed'

    @pytest.mark.asyncio
    async def test_send_message_broadcast(self, manager):
        sent = []

        class FakeConn:
            id = 'b1'

            async def send(self, data, opcode=1):
                sent.append(data)

        manager.ws_connections['b1'] = FakeConn()
        template = Template(template='<html><head></head><body></body></html>')
        manager.add_session('b1', template, Window(), '/')
        await manager.send_message(data={'ping': 1}, session_id=None)
        assert sent
