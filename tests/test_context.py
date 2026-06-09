import pytest
from pyweber.models.context import (
    get_current_request,
    get_current_window,
    set_current_request,
    reset_current_request,
    set_current_window,
    reset_current_window,
)
from pyweber.core.window import Window
from pyweber.models.cookies import CookieManager


class TestRequestContext:
    def test_request_context_isolated(self):
        req_a = object()
        req_b = object()

        token_a = set_current_request(req_a)
        assert get_current_request() is req_a

        token_b = set_current_request(req_b)
        assert get_current_request() is req_b

        reset_current_request(token_b)
        assert get_current_request() is req_a

        reset_current_request(token_a)
        assert get_current_request() is None


class TestWindowContext:
    def test_window_context_isolated(self):
        win_a = Window()
        win_a.session_id = 'session-a'
        win_b = Window()
        win_b.session_id = 'session-b'

        token_a = set_current_window(win_a)
        assert get_current_window() is win_a

        token_b = set_current_window(win_b)
        assert get_current_window() is win_b

        reset_current_window(token_b)
        assert get_current_window() is win_a

        reset_current_window(token_a)
        assert get_current_window() is None


class TestCookieManagerClear:
    def test_clear_removes_accumulated_cookies(self):
        manager = CookieManager()
        manager.set_cookie('user', 'joao')
        manager.set_cookie('theme', 'dark')
        assert len(manager.cookies) == 2

        manager.clear()
        assert manager.cookies == {}
