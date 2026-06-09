import pytest
from unittest.mock import Mock

import pyweber as pw
from pyweber.models.context import set_current_window, reset_current_window
from pyweber.core.window import Window
from pyweber.connection.session import sessions, Session


class TestPublicSessionApi:
    def test_session_id_from_window_context(self):
        win = Window()
        win.session_id = 'public-session'
        token = set_current_window(win)
        try:
            assert pw.session_id() == 'public-session'
        finally:
            reset_current_window(token)

    def test_session_returns_session_object(self):
        win = Window()
        template = Mock()
        sessions.add_session(
            'public-session',
            Session(template=template, window=win, session_id='public-session', current_route='/'),
        )
        win.session_id = 'public-session'
        token = set_current_window(win)
        try:
            result = pw.session()
            assert result.session_id == 'public-session'
        finally:
            reset_current_window(token)
            sessions.remove_session('public-session')

    def test_session_id_without_context_returns_none(self):
        assert pw.session_id() is None
        assert pw.session() is None
