import pytest
from unittest.mock import Mock, patch

from pyweber.core.window import (
    Window,
    Screen,
    Location,
    Orientation,
    LocalStorage,
    SessionStorage,
    Confirm,
    Prompt,
    window,
)
from pyweber.models.context import get_current_window, set_current_window, reset_current_window
from pyweber.utils.types import OrientationType, WindowEventType


class TestWindowBasics:
    def test_window_defaults(self):
        w = Window()
        assert w.width == 0.0
        assert w.session_id is None
        assert isinstance(w.events, object)

    def test_add_and_get_event(self):
        w = Window()
        called = []

        def on_load(e):
            called.append(True)

        w.add_event(WindowEventType.LOAD, on_load)
        assert w.get_event('load') is on_load

    def test_remove_event(self):
        w = Window()
        w.add_event(WindowEventType.LOAD, lambda e: None)
        w.remove_event(WindowEventType.LOAD)
        assert w.get_event('load') is None


class TestWindowProxy:
    def test_proxy_reads_active_context(self):
        w = Window()
        w.session_id = 'ctx-session'
        token = set_current_window(w)
        try:
            assert window.session_id == 'ctx-session'
        finally:
            reset_current_window(token)

    def test_proxy_raises_without_context(self):
        with pytest.raises(RuntimeError, match='No active window context'):
            _ = window.width


class TestStorageClasses:
    @patch('asyncio.run')
    def test_local_storage_set(self, mock_run):
        ws = Mock()
        storage = LocalStorage(data={}, session_id='s1', ws=ws)
        storage.set('key', 'value')
        assert storage.data['key'] == 'value'

    @patch('asyncio.run')
    def test_session_storage_pop(self, mock_run):
        ws = Mock()
        storage = SessionStorage(data={'k': 'v'}, session_id='s1', ws=ws)
        assert storage.pop('k') == 'v'


class TestConfirmPrompt:
    def test_confirm_repr(self):
        assert 'result' in repr(Confirm('yes', 'id-1'))

    def test_prompt_repr(self):
        assert 'result' in repr(Prompt('answer', 'id-2'))


class TestWindowTimers:
    def _patch_send(self, w: Window):
        w._Window__ws = Mock()
        return patch.object(w, '__send__')

    def test_set_timeout_registers_and_sends(self):
        w = Window()
        with patch.object(w, '__send__') as mock_send:
            timer_id = w.set_timeout(lambda: None, 100)
            assert isinstance(timer_id, str)
            data = mock_send.call_args.kwargs['data']
            assert data['set_timeout']['id'] == timer_id
            assert data['set_timeout']['delay'] == 100
            assert w.take_timer_callback(timer_id) is not None

    def test_set_interval_keeps_callback(self):
        w = Window()
        cb = lambda: None
        with patch.object(w, '__send__'):
            interval_id = w.set_interval(cb, 50)
        assert w.is_interval_id(interval_id)
        assert w.take_timer_callback(interval_id, keep=True) is cb
        assert w.take_timer_callback(interval_id, keep=True) is cb

    def test_clear_timeout(self):
        w = Window()
        with patch.object(w, '__send__') as mock_send:
            timer_id = w.set_timeout(lambda: None, 10)
            w.clear_timeout(timer_id)
            assert w.take_timer_callback(timer_id) is None
            assert mock_send.call_args.kwargs['data'] == {'clear_timeout': {'id': timer_id}}

    def test_request_animation_frame(self):
        w = Window()
        with patch.object(w, '__send__') as mock_send:
            frame_id = w.request_animation_frame(lambda: None)
            assert mock_send.call_args.kwargs['data']['request_animation_frame']['id'] == frame_id

    def test_scroll_by_sends_delta(self):
        w = Window()
        w.scroll_x = 10
        w.scroll_y = 20
        with patch.object(w, '__send__') as mock_send:
            w.scroll_by(5, 7)
            assert mock_send.call_args.kwargs['data'] == {
                'scroll_by': {'x': 5, 'y': 7, 'behavior': 'instant'}
            }
        assert w.scroll_x == 15
        assert w.scroll_y == 27

@pytest.mark.asyncio
async def test_timer_response_does_not_resolve_confirm_future():
    import asyncio
    from unittest.mock import MagicMock

    from pyweber.connection.websocket import BaseWebsockets
    from pyweber.connection.session import Session, sessions

    app = MagicMock()
    ws = BaseWebsockets(app=app)
    session_id = 'timer-session'
    w = Window()
    w.session_id = session_id
    fired = []
    timer_id = 'tid-1'
    w._Window__timer_callbacks[timer_id] = lambda: fired.append(True)

    sessions.add_session(
        session_id,
        Session(template=MagicMock(), window=w, session_id=session_id, current_route='/'),
    )
    try:
        loop = asyncio.get_running_loop()
        fut = loop.create_future()
        ws._window_response_future[session_id] = fut

        await ws.set_window_response(
            {'timeout_completed': True, 'timeout_id': timer_id},
            session_id,
        )
        assert fired == [True]
        assert not fut.done()
    finally:
        sessions.remove_session(session_id)
