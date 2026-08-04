"""Identity-preserving sync: self / subclasses survive WS connect merge."""

from __future__ import annotations

from unittest.mock import Mock

import pytest

from pyweber.connection.session import sessions
from pyweber.core.element import Element
from pyweber.core.events import TemplateEvents
from pyweber.core.template import Template
from pyweber.models.dom_merge import merge_client_dom, index_elements_by_uuid
from pyweber.models.handoff import TemplateHandoffRegistry, handoff_registry
from pyweber.models.ws_message import wsMessage
from pyweber.services.template_service import TemplateService


@pytest.fixture(autouse=True)
def _clear_sessions_and_handoff():
    handoff_registry.clear()
    for sid in list(sessions.all_sessions):
        sessions.remove_session(sid)
    yield
    handoff_registry.clear()
    for sid in list(sessions.all_sessions):
        sessions.remove_session(sid)


def _window_data():
    return {
        'width': 100,
        'height': 100,
        'innerWidth': 100,
        'innerHeight': 100,
        'scrollX': 0,
        'scrollY': 0,
        'screen': {},
        'location': {},
        'sessionStorage': {},
        'localStorage': {},
    }


class Counter(Element):
    def __init__(self):
        self.label = Element('span', id='n', content='0')
        btn = Element(
            'button',
            id='inc',
            content='+',
            events=TemplateEvents(onclick=self.inc),
        )
        super().__init__('div', id='counter', childs=[self.label, btn])
        self.clicks = 0

    def inc(self, e=None):
        self.clicks += 1
        self.label.content = str(int(self.label.content or '0') + 1)


class Page(Template):
    def __init__(self):
        self.counter = Counter()
        html = (
            '<html><head></head><body>'
            f'<div id="wrap">{self.counter.to_html()}</div>'
            '</body></html>'
        )
        # Build via Element tree so counter identity is kept after adopt-style wrap
        super().__init__(template='<html><head></head><body></body></html>')
        body = self.body
        while body.childs:
            body.childs.pop()
        body.content = None
        wrap = Element('div', id='wrap', childs=[self.counter])
        body.add_child(wrap)


class TestDomMerge:
    def test_merge_preserves_server_element_identity(self):
        server = Element.from_html(
            '<html><body><input uuid="u1" id="name" value="old"/></body></html>'
        )
        original_input = index_elements_by_uuid(server)['u1']
        client = (
            '<html uuid="h"><body uuid="b">'
            '<input uuid="u1" id="name" value="typed"/>'
            '</body></html>'
        )
        merge_client_dom(server, client)
        assert index_elements_by_uuid(server)['u1'] is original_input
        assert original_input.value == 'typed'

    def test_merge_grafts_client_only_node(self):
        server = Element.from_html(
            '<html uuid="h"><body uuid="b"><div uuid="box" id="box">x</div></body></html>'
        )
        box = index_elements_by_uuid(server)['box']
        client = (
            '<html uuid="h"><body uuid="b">'
            '<div uuid="box" id="box">x<span uuid="js" id="injected">JS</span></div>'
            '</body></html>'
        )
        merge_client_dom(server, client)
        assert index_elements_by_uuid(server)['box'] is box
        injected = index_elements_by_uuid(server).get('js')
        assert injected is not None
        assert injected.id == 'injected'
        assert injected.parent is box


class TestHandoffMove:
    def test_consume_moves_same_instance(self):
        registry = TemplateHandoffRegistry()
        page = Page()
        token = registry.create(page, '/c')
        got = registry.consume(token, '/c')
        assert got is page
        assert isinstance(got, Page)
        assert registry.consume(token, '/c') is None

    def test_element_clone_preserves_subclass_and_refs(self):
        c = Counter()
        label_uuid = c.label.uuid
        cloned = c.clone
        assert type(cloned) is Counter
        assert cloned.uuid == c.uuid
        assert cloned.label is not c.label
        assert cloned.label.uuid == label_uuid
        assert cloned.label is index_elements_by_uuid(cloned)[label_uuid]


class TestEnsureAdopt:
    def test_adopt_element_keeps_identity(self):
        counter = Counter()
        tpl = TemplateService()._adopt_element_as_template(counter)
        assert isinstance(tpl, Template)
        found = tpl.querySelector('#counter')
        assert found is counter


class TestSelfAfterWsConnect:
    @pytest.mark.asyncio
    async def test_self_refs_work_after_client_html_merge(self):
        page = Page()
        counter = page.counter
        label = counter.label
        token = handoff_registry.create(page, '/page')

        client_html = page.build_html()
        # Strip doctype noise; outerHTML-like
        if client_html.startswith('<!DOCTYPE'):
            client_html = client_html.split('\n', 1)[-1]

        raw = {
            'type': None,
            'event_ref': None,
            'route': '/page',
            'target_uuid': None,
            'current_target_uuid': None,
            'template': client_html,
            'values': {},
            'event_data': {},
            'window_data': _window_data(),
            'window_response': {},
            'window_event': None,
            'sessionId': 'sess-self',
            'file_content': {},
            'handoffToken': token,
        }
        msg = wsMessage(raw_message=raw, app=Mock(), ws=Mock())
        template = await msg.template

        assert template is page
        assert page.counter is counter
        assert counter.label is label

        counter.inc()
        assert label.content == '1'
        assert counter.clicks == 1
        # Live tree still has the same label
        assert template.querySelector('#n') is label
