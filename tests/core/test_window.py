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
