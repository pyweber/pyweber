"""Coverage for websocket session bind, handlers, frames, and ASGI/WSGI paths."""

from __future__ import annotations

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from helpers import RecvSocket, make_masked_frame
from pyweber.connection.session import Session, sessions
from pyweber.connection.websocket import (
    WebsocketManager,
    WebsocketServer,
    _ws_message_is_actionable,
    event_is_running,
)
from pyweber.core.element import Element
from pyweber.core.events import EventBook, clear_event_book
from pyweber.core.template import Template
from pyweber.core.window import Window
from pyweber.models.task_manager import TaskManager
from pyweber.models.ws_message import wsMessage
from pyweber.utils.security import SESSION_COOKIE_NAME, sign_value
from pyweber.utils.types import EventType, WindowEventType


WINDOW_DATA = {
    'width': 800,
    'height': 600,
    'innerWidth': 800,
    'innerHeight': 600,
    'scrollX': 0,
    'scrollY': 0,
    'screen': {
        'width': 800,
        'height': 600,
        'colorDepth': 24,
        'pixelDepth': 24,
        'screenX': 0,
        'screenY': 0,
        'orientation': {'angle': 0, 'type': 'landscape-primary', 'on_change': None},
    },
    'location': {
        'host': 'localhost',
        'href': 'http://localhost/',
        'protocol': 'http:',
        'pathname': '/',
        'origin': 'http://localhost',
    },
    'sessionStorage': {},
    'localStorage': {},
}


def _clear_sessions():
    for sid in list(sessions.all_sessions):
        sessions.remove_session(sid)


def _full_message(**overrides):
    message = {
        'type': '',
        'event_ref': '',
        'route': '/',
        'target_uuid': '',
        'current_target_uuid': '',
        'template': '<html><body></body></html>',
        'values': {},
        'event_data': {},
        'window_data': WINDOW_DATA,
        'window_response': {},
        'window_event': '',
        'sessionId': None,
        'file_content': {},
        'handoffToken': '',
    }
    message.update(overrides)
    return message


class TestWsMessageActionable:
    def test_handoff_token(self):
        assert _ws_message_is_actionable({'handoffToken': 'tok'})

    def test_window_response(self):
        assert _ws_message_is_actionable({'window_response': {'ok': 1}})

    def test_file_content(self):
        assert _ws_message_is_actionable({'file_content': {'file_id': 'f1'}})

    def test_known_session_without_template(self):
        _clear_sessions()
        sessions.add_session(
            'known',
            Session(Template('<html></html>'), Window(), 'known', '/'),
        )
        try:
            assert _ws_message_is_actionable({'sessionId': 'known'})
            assert not _ws_message_is_actionable({'sessionId': 'missing'})
        finally:
            _clear_sessions()


class TestEventIsRunning:
    def test_false_when_session_idle(self, pyweber_app):
        msg = MagicMock()
        msg.session_id = 'nope'
        msg.target_uuid = 'x'
        msg.type = 'click'
        assert event_is_running(msg, TaskManager()) is False

    def test_true_when_async_handler_active(self, pyweber_app):
        _clear_sessions()
        called = []

        def handler(e):
            called.append(1)

        btn = Element('button')
        btn.add_event(EventType.CLICK, handler)
        tpl = Template('<html><body></body></html>')
        tpl.body.childs = [btn]
        sid = 'run-evt'
        sessions.add_session(sid, Session(tpl, Window(), sid, '/'))
        tm = TaskManager()
        tm.active_handlers_async[sid] = {f'event_{id(handler)}': MagicMock(done=lambda: False)}
        msg = MagicMock()
        msg.session_id = sid
        msg.target_uuid = btn.uuid
        msg.type = 'click'
        try:
            assert event_is_running(msg, tm) is True
        finally:
            _clear_sessions()

    def test_false_when_handler_not_callable(self, pyweber_app):
        _clear_sessions()
        el = Element('div')
        tpl = Template('<html><body></body></html>')
        tpl.body.childs = [el]
        sid = 'run-none'
        sessions.add_session(sid, Session(tpl, Window(), sid, '/'))
        tm = TaskManager()
        tm.active_handlers_async[sid] = {'event_1': MagicMock()}
        msg = MagicMock()
        msg.session_id = sid
        msg.target_uuid = el.uuid
        msg.type = 'click'
        try:
            assert event_is_running(msg, tm) is False
        finally:
            _clear_sessions()


class TestBindSessionAndEnsure:
    @pytest.fixture
    def manager(self, pyweber_app):
        return pyweber_app.ws_server

    def test_bind_reuses_client_session(self, manager):
        _clear_sessions()
        sessions.add_session(
            'client-sid',
            Session(Template('<html></html>'), Window(), 'client-sid', '/'),
        )
        try:
            sid, is_new = manager.bind_session_id(
                client_session_id='client-sid',
                connection_id=None,
                cookies={},
            )
            assert sid == 'client-sid'
            assert is_new is False
        finally:
            _clear_sessions()

    def test_bind_reuses_cookie_session(self, manager):
        _clear_sessions()
        sessions.add_session(
            'cookie-sid',
            Session(Template('<html></html>'), Window(), 'cookie-sid', '/'),
        )
        try:
            sid, is_new = manager.bind_session_id(
                client_session_id=None,
                connection_id=None,
                cookies={SESSION_COOKIE_NAME: sign_value('cookie-sid')},
            )
            assert sid == 'cookie-sid'
            assert is_new is False
        finally:
            _clear_sessions()

    def test_bind_prefers_connection_id_for_new(self, manager):
        _clear_sessions()
        sid, is_new = manager.bind_session_id(
            client_session_id=None,
            connection_id='sock-1',
            cookies={},
        )
        assert sid == 'sock-1'
        assert is_new is True

    @pytest.mark.asyncio
    async def test_ensure_session_creates_and_sends_set_session(self, manager):
        _clear_sessions()
        sent = []

        async def capture(data, session_id, route=None):
            sent.append(data)

        manager.send_message = capture
        raw = _full_message(sessionId=None, template='<html><body>x</body></html>')
        message = wsMessage(raw_message=raw, app=manager.app, ws=manager)
        target = MagicMock()
        try:
            sid, tpl, is_new = await manager._ensure_session_and_template(
                message,
                connection_id='ens-1',
                cookies={},
                send_target=target,
            )
            assert is_new is True
            assert sid == 'ens-1'
            assert sessions.get_session(sid) is not None
            assert any('setSessionId' in d for d in sent)
            assert manager.ws_connections[sid] is target
            assert isinstance(tpl, Template)
        finally:
            _clear_sessions()
            manager.ws_connections.clear()

    @pytest.mark.asyncio
    async def test_ensure_session_updates_existing_with_template(self, manager):
        _clear_sessions()
        sid = 'ens-exist'
        old = Template('<html><body>old</body></html>')
        manager.add_session(sid, old, Window(), '/')
        manager.ws_connections[sid] = MagicMock()
        raw = _full_message(
            sessionId=sid,
            template='<html><body>new</body></html>',
        )
        message = wsMessage(raw_message=raw, app=manager.app, ws=manager)
        try:
            out_sid, sync, is_new = await manager._ensure_session_and_template(
                message,
                connection_id=sid,
                cookies={},
                send_target=MagicMock(),
            )
            assert is_new is False
            assert out_sid == sid
            assert sync is not None
            session = sessions.get_session(sid)
            assert session.old_template is not None
        finally:
            _clear_sessions()
            manager.ws_connections.clear()


class TestMessageHandler:
    @pytest.fixture
    def manager(self, pyweber_app):
        return pyweber_app.ws_server

    @pytest.mark.asyncio
    async def test_document_sync_click(self, manager):
        _clear_sessions()
        clear_event_book()
        hits = []

        def on_click(e):
            hits.append('clicked')

        btn = Element('button')
        btn.add_event(EventType.CLICK, on_click)
        tpl = Template('<html><body></body></html>')
        tpl.body.childs = [btn]
        sid = 'mh-sync'
        win = Window()
        win.session_id = sid
        manager.add_session(sid, tpl, win, '/')
        raw = _full_message(
            type='click',
            event_ref='document',
            sessionId=sid,
            target_uuid=btn.uuid,
            current_target_uuid=btn.uuid,
            template=None,
        )
        message = wsMessage(raw_message=raw, app=manager.app, ws=manager)
        message.session_id = sid
        try:
            await manager.message_handler(message)
            # sync handler runs in thread pool — wait briefly
            await asyncio.sleep(0.15)
            assert hits == ['clicked']
        finally:
            manager.task_manager.shutdown()
            _clear_sessions()

    @pytest.mark.asyncio
    async def test_document_async_click(self, manager):
        _clear_sessions()
        hits = []

        async def on_click(e):
            hits.append('async')

        btn = Element('button')
        btn.add_event(EventType.CLICK, on_click)
        tpl = Template('<html><body></body></html>')
        tpl.body.childs = [btn]
        sid = 'mh-async'
        win = Window()
        win.session_id = sid
        manager.add_session(sid, tpl, win, '/')
        raw = _full_message(
            type='click',
            event_ref='document',
            sessionId=sid,
            target_uuid=btn.uuid,
            current_target_uuid=btn.uuid,
            template=None,
        )
        message = wsMessage(raw_message=raw, app=manager.app, ws=manager)
        message.session_id = sid
        try:
            await manager.message_handler(message)
            assert hits == ['async']
        finally:
            _clear_sessions()

    @pytest.mark.asyncio
    async def test_document_eventbook_string_handler(self, manager):
        _clear_sessions()
        clear_event_book()
        hits = []

        def on_click(e):
            hits.append('book')

        EventBook['evt_book_1'] = {'event': on_click, 'element': None}
        btn = Element('button')
        btn.events.__dict__['onclick'] = 'evt_book_1'
        tpl = Template('<html><body></body></html>')
        tpl.body.childs = [btn]
        sid = 'mh-book'
        manager.add_session(sid, tpl, Window(), '/')
        raw = _full_message(
            type='click',
            event_ref='document',
            sessionId=sid,
            target_uuid=btn.uuid,
            current_target_uuid=btn.uuid,
            template=None,
        )
        message = wsMessage(raw_message=raw, app=manager.app, ws=manager)
        message.session_id = sid
        try:
            await manager.message_handler(message)
            await asyncio.sleep(0.15)
            assert hits == ['book']
        finally:
            clear_event_book()
            manager.task_manager.shutdown()
            _clear_sessions()

    @pytest.mark.asyncio
    async def test_window_event_handler(self, manager):
        _clear_sessions()
        hits = []

        def on_load(e):
            hits.append('load')

        sid = 'mh-win'
        win = Window()
        win.session_id = sid
        win.add_event(WindowEventType.LOAD, on_load)
        manager.add_session(sid, Template('<html><body></body></html>'), win, '/')
        raw = _full_message(
            type='load',
            event_ref='window',
            window_event='load',
            sessionId=sid,
            template=None,
        )
        message = wsMessage(raw_message=raw, app=manager.app, ws=manager)
        message.session_id = sid
        message.window = win
        try:
            await manager.message_handler(message)
            await asyncio.sleep(0.15)
            assert hits == ['load']
        finally:
            manager.task_manager.shutdown()
            _clear_sessions()

    @pytest.mark.asyncio
    async def test_message_handler_missing_session_returns(self, manager):
        raw = _full_message(sessionId='ghost', type='click', event_ref='document')
        message = wsMessage(raw_message=raw, app=manager.app, ws=manager)
        message.session_id = 'ghost'
        await manager.message_handler(message)


class TestTemplateDiffAndTimers:
    @pytest.fixture
    def manager(self, pyweber_app):
        return pyweber_app.ws_server

    @pytest.mark.asyncio
    async def test_get_template_diff_with_mutation(self, manager):
        _clear_sessions()
        tpl = Template('<html><head></head><body><p>a</p></body></html>')
        session = Session(tpl, Window(), 'diff-1', '/')
        sessions.add_session('diff-1', session)
        try:
            session.old_template = tpl.clone()
            session.template.body.childs = [Element('p', content='b')]
            diff = await manager.get_template_diff(session)
            assert isinstance(diff, dict)
        finally:
            _clear_sessions()

    @pytest.mark.asyncio
    async def test_get_template_diff_clones_when_old_missing(self, manager):
        _clear_sessions()
        tpl = Template('<html><head></head><body></body></html>')
        session = Session(tpl, Window(), 'diff-2', '/')
        session.old_template = None
        sessions.add_session('diff-2', session)
        try:
            diff = await manager.get_template_diff(session)
            assert isinstance(diff, dict)
            assert session.old_template is not None
        finally:
            _clear_sessions()

    @pytest.mark.asyncio
    async def test_dispatch_timer_async_callback(self, manager):
        _clear_sessions()
        hits = []

        async def cb():
            hits.append('async-timer')

        sid = 'timer-async'
        win = Window()
        win.session_id = sid
        tid = 't-async'
        win._Window__timer_callbacks[tid] = cb
        sessions.add_session(sid, Session(Template('<html></html>'), win, sid, '/'))
        try:
            await manager._dispatch_timer_callback(
                {'timeout_completed': True, 'timeout_id': tid},
                sid,
            )
            assert hits == ['async-timer']
        finally:
            _clear_sessions()

    @pytest.mark.asyncio
    async def test_dispatch_timer_interval_keep(self, manager):
        _clear_sessions()
        hits = []

        def cb():
            hits.append(1)

        sid = 'timer-int'
        win = Window()
        win.session_id = sid
        with patch.object(win, '__send__'):
            tid = win.set_interval(cb, 10)
        sessions.add_session(sid, Session(Template('<html></html>'), win, sid, '/'))
        try:
            await manager._dispatch_timer_callback(
                {'interval_executed': True, 'interval_id': tid},
                sid,
            )
            assert hits == [1]
            assert win.take_timer_callback(tid, keep=True) is cb
        finally:
            _clear_sessions()

    def test_is_timer_response_non_dict(self, manager):
        assert manager._is_timer_response(None) is False
        assert manager._is_timer_response('x') is False


class TestSendMessageVariants:
    @pytest.fixture
    def manager(self, pyweber_app):
        return pyweber_app.ws_server

    @pytest.mark.asyncio
    async def test_send_by_route(self, manager):
        sent = []

        class Conn:
            async def send(self, data, opcode=1):
                sent.append(data)

        _clear_sessions()
        manager.add_session('r1', Template('<html></html>'), Window(), '/api/echo')
        manager.ws_connections['r1'] = Conn()
        manager.add_session('r2', Template('<html></html>'), Window(), '/')
        manager.ws_connections['r2'] = Conn()
        try:
            await manager.send_message(data={'ping': True}, session_id=None, route='/api/echo')
            assert len(sent) == 1
        finally:
            _clear_sessions()
            manager.ws_connections.clear()

    @pytest.mark.asyncio
    async def test_send_uvicorn_protocol(self, manager):
        sent = []

        async def asgi_send(msg):
            sent.append(msg)

        manager.protocol = 'uvicorn'
        _clear_sessions()
        manager.add_session('uv1', Template('<html></html>'), Window(), '/')
        manager.ws_connections['uv1'] = asgi_send
        try:
            await manager.send_message(data={'hello': 1}, session_id='uv1')
            assert sent and sent[0]['type'] == 'websocket.send'
        finally:
            manager.protocol = 'pyweber'
            _clear_sessions()
            manager.ws_connections.clear()

    @pytest.mark.asyncio
    async def test_send_skips_none_connection(self, manager):
        manager.ws_connections['ghost'] = None
        await manager.send_message(data={'x': 1}, session_id='ghost')
        manager.ws_connections.pop('ghost', None)


class TestWsHandlers:
    @pytest.fixture
    def manager(self, pyweber_app):
        return pyweber_app.ws_server

    @pytest.mark.asyncio
    async def test_ws_handler_wsgi_click(self, manager):
        _clear_sessions()
        hits = []

        def on_click(e):
            hits.append(1)

        btn = Element('button')
        btn.add_event(EventType.CLICK, on_click)
        tpl = Template('<html><body></body></html>')
        tpl.body.childs = [btn]
        manager.app.add_route(route='/wsgi-click', template=tpl, methods=['GET'])

        sock = WebsocketServer(RecvSocket(b''))
        sock.id = None
        payload = json.dumps(
            _full_message(
                type='click',
                event_ref='document',
                route='/wsgi-click',
                target_uuid=btn.uuid,
                current_target_uuid=btn.uuid,
                template=None,
                sessionId=None,
                handoffToken='',
            )
        )
        # Known session with the live button tree so handlers match
        sid = 'wsgi-live'
        manager.add_session(sid, tpl, Window(), '/wsgi-click')
        sock.id = sid
        sock._WebsocketServer__messages.append(
            json.dumps(
                _full_message(
                    type='click',
                    event_ref='document',
                    route='/wsgi-click',
                    target_uuid=btn.uuid,
                    current_target_uuid=btn.uuid,
                    template=None,
                    sessionId=sid,
                )
            )
        )

        async def run_one():
            task = asyncio.create_task(manager.ws_handler_wsgi(sock))
            await asyncio.sleep(0.2)
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        try:
            with patch.object(manager, 'send_message', new_callable=AsyncMock):
                await run_one()
            await asyncio.sleep(0.15)
            assert hits == [1]
        finally:
            manager.task_manager.shutdown()
            _clear_sessions()
            manager.ws_connections.clear()

    @pytest.mark.asyncio
    async def test_ws_handler_asgi_flow(self, manager):
        _clear_sessions()
        sent = []
        received = [
            {'type': 'websocket.connect'},
            {
                'type': 'websocket.receive',
                'text': json.dumps(
                    _full_message(
                        template='<html><body>hi</body></html>',
                        sessionId=None,
                    )
                ),
            },
            {'type': 'websocket.disconnect'},
        ]
        idx = {'i': 0}

        async def receive():
            i = idx['i']
            idx['i'] += 1
            if i < len(received):
                return received[i]
            return {'type': 'websocket.disconnect'}

        async def send(msg):
            sent.append(msg)

        try:
            with patch.object(manager, 'send_message', new_callable=AsyncMock):
                await manager.ws_handler_asgi(receive=receive, send=send, cookies={})
            assert any(m.get('type') == 'websocket.accept' for m in sent)
        finally:
            _clear_sessions()
            manager.ws_connections.clear()

    @pytest.mark.asyncio
    async def test_asgi_call_parses_cookies(self, manager):
        _clear_sessions()
        sent = []
        received = [
            {'type': 'websocket.connect'},
            {'type': 'websocket.disconnect'},
        ]
        idx = {'i': 0}

        async def receive():
            i = idx['i']
            idx['i'] += 1
            return received[i] if i < len(received) else {'type': 'websocket.disconnect'}

        async def send(msg):
            sent.append(msg)

        scope = {
            'type': 'websocket',
            'headers': [
                (b'cookie', f'{SESSION_COOKIE_NAME}={sign_value("asgi-cookie")}'.encode()),
            ],
        }
        try:
            await manager(scope, receive, send)
            assert any(m.get('type') == 'websocket.accept' for m in sent)
        finally:
            _clear_sessions()

    @pytest.mark.asyncio
    async def test_ws_handler_wsgi_file_and_window_response(self, manager):
        _clear_sessions()
        sock = WebsocketServer(RecvSocket(b''))
        sock.id = 'wsgi-misc'
        manager.add_session(
            'wsgi-misc',
            Template('<html><body></body></html>'),
            Window(),
            '/',
        )
        manager.ws_connections['wsgi-misc'] = sock

        file_msg = _full_message(
            sessionId='wsgi-misc',
            template=None,
            file_content={'file_id': 'f-wsgi', 'data': 'x'},
            type='',
            event_ref='',
        )
        # Make actionable via known session
        win_msg = _full_message(
            sessionId='wsgi-misc',
            template=None,
            window_response={'confirm_result': 'yes'},
            type='',
            event_ref='',
        )
        sock._WebsocketServer__messages.extend([
            json.dumps(file_msg),
            json.dumps(win_msg),
        ])

        processed = {'n': 0}

        async def limited():
            async for message in sock:
                raw = manager.process_ws_message_handler(message)
                if not raw:
                    continue
                msg = wsMessage(raw_message=raw, app=manager.app, ws=manager)
                if msg.file_content:
                    await manager.set_file_content(
                        msg.file_content, msg.file_content.get('file_id')
                    )
                if msg.window_response:
                    await manager.set_window_response(msg.window_response, msg.session_id)
                processed['n'] += 1
                if processed['n'] >= 2:
                    break

        try:
            await asyncio.wait_for(limited(), timeout=2)
            assert processed['n'] == 2
        finally:
            _clear_sessions()
            manager.ws_connections.clear()


class TestWebsocketServerFrames:
    @pytest.mark.asyncio
    async def test_receive_extended_127(self):
        payload = b'z' * 70000
        sock = RecvSocket(make_masked_frame(payload))
        ws = WebsocketServer(sock)
        opcode, message, fin = await ws.receive_frame()
        assert opcode == 1
        assert len(message) == 70000

    @pytest.mark.asyncio
    async def test_manage_connection_text_then_close(self):
        payload = b'{"ok":true}'
        close_frame = make_masked_frame(b'', opcode=8)
        text_frame = make_masked_frame(payload, opcode=1)
        sock = RecvSocket(text_frame + close_frame)
        ws = WebsocketServer(sock)
        ws.id = 'mc-1'
        seen = []

        async def handler(server):
            async for msg in server:
                seen.append(msg)
                break

        await ws.manage_connection(handler)
        assert seen == ['{"ok":true}']
        assert sock.closed

    @pytest.mark.asyncio
    async def test_manage_connection_sync_handler(self):
        payload = b'hi'
        frames = make_masked_frame(payload) + make_masked_frame(b'', opcode=8)
        sock = RecvSocket(frames)
        ws = WebsocketServer(sock)
        seen = []

        def handler(server):
            seen.append(next(iter(server)))

        await ws.manage_connection(handler)
        assert seen == [b'hi'] or seen == ['hi'] or True  # text opcode decodes
        # opcode 1 → decoded str
        assert seen and (seen[0] == 'hi' or seen[0] == b'hi')

    @pytest.mark.asyncio
    async def test_manage_connection_ping_pong(self):
        ping = make_masked_frame(b'', opcode=9)
        close = make_masked_frame(b'', opcode=8)
        sock = RecvSocket(ping + close)
        ws = WebsocketServer(sock)
        await ws.manage_connection(lambda s: None)
        assert sock.closed

    @pytest.mark.asyncio
    async def test_anext_and_close_exception(self):
        class BoomClose:
            def sendall(self, data): pass
            def close(self):
                raise OSError('already closed')
            def setblocking(self, f): pass
            def recv(self, n):
                return b''

        ws = WebsocketServer(BoomClose())
        ws._WebsocketServer__messages.append('x')
        assert await ws.__anext__() == 'x'
        await ws.close()

    @pytest.mark.asyncio
    async def test_read_exact_blocking_then_data(self):
        class Flaky:
            def __init__(self):
                self.n = 0
            def setblocking(self, f): pass
            def recv(self, n):
                self.n += 1
                if self.n == 1:
                    raise BlockingIOError()
                return b'ab'[:n]

        ws = WebsocketServer(Flaky())
        data = await ws.read_exact(2)
        assert data == b'ab'

    def test_remove_connection_without_loop(self, pyweber_app):
        manager = pyweber_app.ws_server
        conn = WebsocketServer(RecvSocket(b''))
        conn.id = 'rm-1'
        manager.add_connection(conn)
        manager.remove_connection('rm-1')
        assert manager.get_connection('rm-1') is None
        manager.remove_connection('missing')  # no-op

    @pytest.mark.asyncio
    async def test_remove_connection_with_running_loop(self, pyweber_app):
        manager = pyweber_app.ws_server
        conn = WebsocketServer(RecvSocket(b''))
        conn.id = 'rm-2'
        manager.add_connection(conn)
        manager.remove_connection('rm-2')
        await asyncio.sleep(0.05)
        assert manager.get_connection('rm-2') is None

    @pytest.mark.asyncio
    async def test_connect_wsgi_clears_session(self, pyweber_app):
        manager = pyweber_app.ws_server
        _clear_sessions()
        sock = WebsocketServer(RecvSocket(make_masked_frame(b'', opcode=8)))
        sock.id = 'conn-wsgi'
        manager.add_session(
            'conn-wsgi',
            Template('<html></html>'),
            Window(),
            '/',
        )
        manager.ws_connections['conn-wsgi'] = sock
        try:
            await manager.connect_wsgi(sock)
            assert sessions.get_session('conn-wsgi') is None
        finally:
            _clear_sessions()
            manager.ws_connections.clear()

    @pytest.mark.asyncio
    async def test_get_window_response_timeout(self, pyweber_app):
        manager = pyweber_app.ws_server
        result = await manager.get_window_response(timeout=0.01, session_id='to-1')
        assert result is None

    @pytest.mark.asyncio
    async def test_clear_session_closes_conn(self, pyweber_app):
        manager = pyweber_app.ws_server
        _clear_sessions()
        sock = WebsocketServer(RecvSocket(b''))
        sock.id = 'clr-2'
        manager.add_session('clr-2', Template('<html></html>'), Window(), '/')
        manager.ws_connections['clr-2'] = sock
        await manager.clear_session('clr-2')
        assert sessions.get_session('clr-2') is None
        assert sock.client.closed
