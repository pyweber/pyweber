import pytest
from unittest.mock import AsyncMock, Mock

from pyweber.core.template import Template
from pyweber.models.handoff import (
    HANDOFF_META_NAME,
    TemplateHandoffRegistry,
    handoff_registry,
    inject_handoff_token,
)
from pyweber.models.request import Request, ClientInfo
from pyweber.models.ws_message import wsMessage
from pyweber.pyweber.pyweber import Pyweber
from pyweber.utils.types import ContentTypes


def _html_page(body: str = 'Hello') -> Template:
    return Template(template=f'<html><head></head><body>{body}</body></html>')


@pytest.fixture(autouse=True)
def clear_handoff_registry():
    handoff_registry.clear()
    yield
    handoff_registry.clear()


class TestTemplateHandoffRegistry:
    def test_create_and_consume_returns_clone(self):
        registry = TemplateHandoffRegistry()
        source = _html_page('one')
        token = registry.create(source, '/page')

        result = registry.consume(token, '/page')

        assert result is not None
        assert result.build_html() == source.build_html()
        assert registry.consume(token, '/page') is None

    def test_consume_rejects_route_mismatch(self):
        registry = TemplateHandoffRegistry()
        token = registry.create(_html_page(), '/expected')

        assert registry.consume(token, '/other') is None

    def test_inject_handoff_token_adds_meta_tag(self):
        template = _html_page()
        inject_handoff_token(template, 'token-123')

        meta = template.querySelector('[name=pyweber-handoff]')
        assert meta is not None
        assert meta.get_attr('content') == 'token-123'


class TestHttpHandoffRegistration:
    @pytest.mark.asyncio
    async def test_get_response_injects_handoff_meta(self):
        app = Pyweber()
        app.add_route(
            route='/dashboard',
            template=lambda **kw: '<html><body>Dashboard</body></html>',
            methods=['GET'],
        )
        req = Request(
            headers='GET /dashboard HTTP/1.1\r\nHost: localhost\r\n\r\n',
            body=b'',
            client_info=ClientInfo(host='127.0.0.1', port=1),
        )

        resp = await app.get_response(req)

        assert resp.status_code == 200
        assert b'name="pyweber-handoff"' in resp.response_content
        assert len(handoff_registry._entries) == 1

    @pytest.mark.asyncio
    async def test_json_response_does_not_inject_handoff(self):
        app = Pyweber()
        app.add_route(route='/api', template={'ok': True}, methods=['GET'], content_type=ContentTypes.json)
        req = Request(
            headers='GET /api HTTP/1.1\r\nHost: localhost\r\n\r\n',
            body=b'',
            client_info=ClientInfo(host='127.0.0.1', port=1),
        )

        resp = await app.get_response(req)

        assert b'pyweber-handoff' not in resp.response_content


class TestWsHandoffConsumption:
    @pytest.mark.asyncio
    async def test_ws_uses_handoff_instead_of_clone_template(self):
        app = Pyweber()
        calls = {'count': 0}

        @app.route('/page')
        def page():
            calls['count'] += 1
            return '<html><body>Rendered once</body></html>'

        req = Request(
            headers='GET /page HTTP/1.1\r\nHost: localhost\r\n\r\n',
            body=b'',
            client_info=ClientInfo(host='127.0.0.1', port=1),
        )
        await app.get_response(req)
        assert calls['count'] == 1

        token = handoff_registry.create(_html_page('from-handoff'), '/page')
        app.clone_template = AsyncMock(side_effect=AssertionError('clone_template should not run'))

        raw_message = {
            'type': None,
            'event_ref': None,
            'route': '/page',
            'target_uuid': None,
            'current_target_uuid': None,
            'template': None,
            'values': {},
            'event_data': {},
            'window_data': {'width': 100, 'height': 100, 'innerWidth': 100, 'innerHeight': 100,
                            'scrollX': 0, 'scrollY': 0, 'screen': {}, 'location': {}, 'sessionStorage': {}, 'localStorage': {}},
            'window_response': {},
            'window_event': None,
            'sessionId': 'new-session',
            'file_content': {},
            'handoffToken': token,
        }

        msg = wsMessage(raw_message=raw_message, app=app, ws=Mock())
        template = await msg.template

        assert 'from-handoff' in template.build_html()
        app.clone_template.assert_not_called()

    @pytest.mark.asyncio
    async def test_ws_falls_back_to_clone_without_token(self):
        app = Pyweber()
        app.add_route(route='/page', template='x', methods=['GET'])
        clone = _html_page('cloned')
        app.clone_template = AsyncMock(return_value=clone)

        raw_message = {
            'type': None,
            'event_ref': None,
            'route': '/page',
            'target_uuid': None,
            'current_target_uuid': None,
            'template': None,
            'values': {},
            'event_data': {},
            'window_data': {'width': 100, 'height': 100, 'innerWidth': 100, 'innerHeight': 100,
                            'scrollX': 0, 'scrollY': 0, 'screen': {}, 'location': {}, 'sessionStorage': {}, 'localStorage': {}},
            'window_response': {},
            'window_event': None,
            'sessionId': 'new-session',
            'file_content': {},
            'handoffToken': None,
        }

        msg = wsMessage(raw_message=raw_message, app=app, ws=Mock())
        template = await msg.template

        assert 'cloned' in template.build_html()
        app.clone_template.assert_awaited_once()
