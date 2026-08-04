"""Tests for 1.6.0.dev2 audit follow-ups."""

from __future__ import annotations

import warnings

import pytest

from pyweber.connection.session import Session, sessions
from pyweber.core.element import Element
from pyweber.core.events import (
    EventBook,
    cleanup_template_events,
    clear_event_book,
    collect_element_uuids,
)
from pyweber.core.events import TemplateEvents
from pyweber.core.template import Template
from pyweber.core.window import Window
from pyweber.utils.security import ensure_safe_redirect_url, is_safe_redirect_url


@pytest.fixture(autouse=True)
def _clear_event_book():
    clear_event_book()
    yield
    clear_event_book()


class TestRedirectSafety:
    def test_relative_ok(self):
        assert is_safe_redirect_url('/dashboard')
        assert ensure_safe_redirect_url('/a/b') == '/a/b'

    def test_rejects_javascript_and_protocol_relative(self):
        assert not is_safe_redirect_url('javascript:alert(1)')
        assert not is_safe_redirect_url('//evil.example/phish')
        with pytest.raises(ValueError):
            ensure_safe_redirect_url('https://evil.example/')

    def test_allowlisted_host(self, monkeypatch):
        monkeypatch.setenv('PYWEBER_ALLOWED_REDIRECT_HOSTS', 'app.example')
        assert is_safe_redirect_url('https://app.example/home')
        assert not is_safe_redirect_url('https://other.example/')

    def test_window_open_rejects_unsafe(self):
        win = Window()
        with pytest.raises(ValueError):
            win.open('https://evil.example/')


class TestEventBookLifecycle:
    def test_cleanup_removes_handlers_for_template_elements(self):
        calls = []

        def handler(e=None):
            calls.append(1)

        btn = Element('button', id='b', events=TemplateEvents(onclick=handler))
        # Force HTML serialization → EventBook registration
        html = btn.to_html()
        assert 'event_' in html or '_onclick' in html
        assert EventBook

        uuids = collect_element_uuids(btn)
        removed = cleanup_template_events(btn)
        assert removed >= 1
        for entry in EventBook.values():
            for uid in entry.get('elements', {}):
                assert uid not in uuids

    def test_session_remove_cleans_eventbook(self):
        def handler(e=None):
            pass

        label = Element('span', id='n', content='0')
        btn = Element('button', events=TemplateEvents(onclick=handler))
        root = Element('div', childs=[label, btn])
        tpl = Template(template='<html><head></head><body></body></html>')
        body = tpl.body
        while body.childs:
            body.childs.pop()
        body.content = None
        body.add_child(root)
        root.to_html()  # register events

        assert EventBook
        sid = 'evt-sess-1'
        sessions.add_session(
            sid,
            Session(template=tpl, window=Window(), session_id=sid, current_route='/'),
        )
        sessions.remove_session(sid)
        # Handlers tied to that tree should be gone
        remaining_uids = set()
        for entry in EventBook.values():
            remaining_uids.update(entry.get('elements', {}).keys())
        assert collect_element_uuids(root).isdisjoint(remaining_uids)


class TestElementUpdateRemoved:
    def test_no_update_method_stub(self):
        el = Element('div')
        assert not hasattr(el, 'update') or not callable(getattr(type(el), 'update', None))
        # Explicit: base Element must not expose NotImplemented update
        assert 'update' not in Element.__dict__


class TestJWTDeprecation:
    def test_public_import_warns(self):
        import pyweber as pw

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter('always')
            # Force module __getattr__
            _ = pw.JWTAlgorithms
        assert any('JWTAlgorithms' in str(w.message) for w in caught)
