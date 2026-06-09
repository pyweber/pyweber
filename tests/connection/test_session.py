import pytest
from unittest.mock import Mock

from pyweber.connection.session import Session, SessionManager, sessions


@pytest.fixture
def session_manager():
    return SessionManager()


@pytest.fixture
def sample_session():
    template = Mock()
    window = Mock()
    return Session(
        template=template,
        window=window,
        session_id='sess-001',
        current_route='/home',
    )


class TestSession:
    def test_session_stores_attributes(self, sample_session):
        assert sample_session.session_id == 'sess-001'
        assert sample_session.current_route == '/home'
        assert sample_session.template is not None
        assert sample_session.window is not None
        assert sample_session.create_at > 0


class TestSessionManager:
    def test_add_get_remove(self, session_manager, sample_session):
        session_manager.add_session('sess-001', sample_session)
        assert session_manager.length == 1
        assert session_manager.get_session('sess-001') is sample_session
        assert 'sess-001' in session_manager.all_sessions

        session_manager.remove_session('sess-001')
        assert session_manager.get_session('sess-001') is None
        assert session_manager.length == 0

    def test_getitem_and_len(self, session_manager, sample_session):
        session_manager.add_session('a', sample_session)
        assert len(session_manager) == 1
        assert session_manager['a'] is sample_session

    def test_global_sessions_singleton(self):
        assert isinstance(sessions, SessionManager)
