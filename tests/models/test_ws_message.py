import pytest
from unittest.mock import Mock, AsyncMock, patch

from pyweber.connection.session import sessions, Session
from pyweber.core.window import Window
from pyweber.models.ws_message import wsMessage


@pytest.fixture
def raw_message():
    return {
        'type': 'click',
        'event_ref': 'document',
        'route': '/',
        'target_uuid': 'target-1',
        'current_target_uuid': 'target-1',
        'template': None,
        'values': {},
        'event_data': {'clientX': 1},
        'window_data': {
            'width': 1920,
            'height': 1080,
            'innerWidth': 1200,
            'innerHeight': 800,
            'scrollX': 0,
            'scrollY': 0,
            'screen': {},
            'location': {'host': 'localhost', 'href': 'http://localhost/', 'protocol': 'http:', 'pathname': '/', 'origin': 'http://localhost'},
            'sessionStorage': {'user': 'joao'},
            'localStorage': {},
        },
        'window_response': {},
        'window_event': None,
        'sessionId': 'session-a',
        'file_content': {},
    }


@pytest.fixture
def ws_manager():
    manager = Mock()
    manager.send_message = AsyncMock()
    return manager


@pytest.fixture
def app():
    mock_app = Mock()
    mock_app.list_routes = ['/']
    mock_app.clone_template = AsyncMock(return_value=Mock(root=Mock(), parse_html=Mock()))
    return mock_app


class TestWsMessage:
    def test_creates_isolated_window_per_session(self, raw_message, app, ws_manager):
        existing = Session(
            template=Mock(),
            window=Window(),
            session_id='session-a',
            current_route='/',
        )
        existing.window.session_storage = Mock()
        sessions.add_session('session-a', existing)

        msg = wsMessage(raw_message=raw_message, app=app, ws=ws_manager)
        assert msg.window is existing.window
        assert msg.window.session_id == 'session-a'
        assert msg.window.session_storage.data == {'user': 'joao'}

        sessions.remove_session('session-a')

    def test_new_session_gets_new_window(self, raw_message, app, ws_manager):
        raw_message['sessionId'] = 'brand-new-session'
        msg = wsMessage(raw_message=raw_message, app=app, ws=ws_manager)
        assert isinstance(msg.window, Window)
        assert msg.window.session_id == 'brand-new-session'

    def test_two_sessions_do_not_share_window(self, raw_message, app, ws_manager):
        msg_a = wsMessage(
            raw_message={**raw_message, 'sessionId': 'user-a', 'window_data': {**raw_message['window_data'], 'sessionStorage': {'user': 'a'}}},
            app=app,
            ws=ws_manager,
        )
        msg_b = wsMessage(
            raw_message={**raw_message, 'sessionId': 'user-b', 'window_data': {**raw_message['window_data'], 'sessionStorage': {'user': 'b'}}},
            app=app,
            ws=ws_manager,
        )
        assert msg_a.window is not msg_b.window
        assert msg_a.window.session_storage.data['user'] == 'a'
        assert msg_b.window.session_storage.data['user'] == 'b'
