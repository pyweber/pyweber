"""Regression: Form/Input trees must clone so WS click events can respond."""

import asyncio
import json
import types

import pyweber as pw
from pyweber.connection.session import sessions
from pyweber.connection.websocket import WebsocketManager
from pyweber.core.events import clear_event_book
from pyweber.models.handoff import handoff_registry
from pyweber.models.ws_message import wsMessage


def _clear_sessions():
    for sid in list(sessions.all_sessions):
        sessions.remove_session(sid)


WINDOW_DATA = {
    'width': 1, 'height': 1, 'innerWidth': 1, 'innerHeight': 1,
    'scrollX': 0, 'scrollY': 0, 'location': {},
    'localStorage': {}, 'sessionStorage': {},
    'screen': {'orientation': {}},
}


class TestFormTemplateCloneEvents:
    def test_home_form_clone_and_click_sends_update(self):
        clear_event_book()
        _clear_sessions()

        app = pw.Pyweber()
        calls = []
        sent = []

        class Home(pw.Template):
            def __init__(self):
                super().__init__('')
                self.body.childs = [
                    title := pw.Element('h1', content='Home Page'),
                    pw.Form(
                        childs=[
                            pw.InputText(name='new_title', placeholder='New page title'),
                            pw.InputButton(
                                name='savebtn',
                                value='Save',
                                style={'cursor': 'pointer'},
                                onclick=self.change_title,
                            ),
                        ]
                    ),
                ]
                self.title_el = title

            def change_title(self, e: pw.EventHandler):
                calls.append('ok')
                e.target.parent.first_child().value = ''
                e.update()

        @app.route('/')
        def index():
            return Home()

        home = Home()
        html = home.build_html()
        token = handoff_registry.create(home, route='/')
        btn = home.getElement(by='attrs', value='name=savebtn')
        assert btn is not None

        # Template with Form must clone (used by get_sync_template on every event)
        cloned = home.clone()
        assert cloned.getElement(by='attrs', value='name=savebtn') is not None

        ws = WebsocketManager(app=app)

        async def capture_send(data, session_id, route=None):
            sent.append({'data': data, 'session_id': session_id})

        ws.send_message = capture_send

        async def run():
            connect = {
                'type': None, 'event_ref': None, 'route': '/',
                'target_uuid': None, 'current_target_uuid': None,
                'template': html, 'values': {}, 'event_data': {},
                'window_data': WINDOW_DATA, 'window_response': {},
                'window_event': None, 'file_content': {},
                'sessionId': None, 'handoffToken': token,
            }
            msg = wsMessage(raw_message=connect, app=app, ws=ws)
            sync = await ws.get_sync_template(message=msg)
            sid = 'test-sid-form-click'
            ws.add_session(session_id=sid, template=sync, window=msg.window, route='/')
            ws.ws_connections[sid] = object()

            live_btn = sessions.get_session(sid).template.getElement(
                by='attrs', value='name=savebtn'
            )
            assert live_btn is not None
            assert callable(live_btn.events.__dict__.get('onclick'))

            click = {
                'type': 'click', 'event_ref': 'document', 'route': '/',
                'target_uuid': live_btn.uuid, 'current_target_uuid': live_btn.uuid,
                'template': None, 'values': {}, 'event_data': {},
                'window_data': WINDOW_DATA, 'window_response': {},
                'window_event': None, 'file_content': {},
                'sessionId': sid, 'handoffToken': None,
            }
            msg2 = wsMessage(raw_message=click, app=app, ws=ws)
            # This used to raise AttributeError on Form.attrs during clone
            sync2 = await ws.get_sync_template(message=msg2)
            ws.update_session(
                session_id=sid, template=sync2, window=msg2.window, route='/'
            )
            await ws.message_handler(message=msg2)
            await asyncio.sleep(0.3)

        asyncio.run(run())

        assert calls == ['ok']
        assert sent and 'template' in sent[0]['data']


class TestCloneTemplateBoundEvents:
    """clone_template fallback must rebind self.handler so e.update() diffs work."""

    def test_clone_template_click_sends_non_empty_diff(self):
        clear_event_book()
        _clear_sessions()

        app = pw.Pyweber()
        calls = []
        diffs = []

        class Home(pw.Template):
            def __init__(self):
                super().__init__('')
                self.body.childs = [
                    title := pw.Element('h1', content='Home Page'),
                    pw.Form(
                        childs=[
                            pw.InputButton(
                                name='savebtn',
                                value='Save',
                                onclick=self.change_title,
                            ),
                        ]
                    ),
                ]
                self.title_el = title
                self.clicks = 0

            def change_title(self, e: pw.EventHandler):
                calls.append('ok')
                self.clicks += 1
                self.title_el.content = f'Changed {self.clicks}'
                e.update()

        @app.route('/')
        def index():
            return Home()

        ws = WebsocketManager(app=app)

        async def capture_send(self, data, session_id, route=None):
            payload = await self.data_to_json(dict(data), session_id=session_id)
            diffs.append(json.loads(payload))

        ws.send_message = types.MethodType(capture_send, ws)

        async def run():
            # No handoff → clone_template path (reconnect / expired token)
            connect = {
                'type': None, 'event_ref': None, 'route': '/',
                'target_uuid': None, 'current_target_uuid': None,
                'template': None, 'values': {}, 'event_data': {},
                'window_data': WINDOW_DATA, 'window_response': {},
                'window_event': None, 'file_content': {},
                'sessionId': None, 'handoffToken': None,
            }
            msg = wsMessage(raw_message=connect, app=app, ws=ws)
            sync = await ws.get_sync_template(message=msg)
            assert isinstance(sync, Home)

            btn = sync.getElement(by='attrs', value='name=savebtn')
            assert btn is not None
            handler = btn.events.onclick
            assert callable(handler)
            assert getattr(handler, '__self__', None) is sync
            assert sync.title_el is sync.querySelector('h1')

            sid = 'test-sid-clone-click'
            ws.add_session(session_id=sid, template=sync, window=msg.window, route='/')
            ws.ws_connections[sid] = object()

            click = {
                'type': 'click', 'event_ref': 'document', 'route': '/',
                'target_uuid': btn.uuid, 'current_target_uuid': btn.uuid,
                'template': None, 'values': {}, 'event_data': {},
                'window_data': WINDOW_DATA, 'window_response': {},
                'window_event': None, 'file_content': {},
                'sessionId': sid, 'handoffToken': None,
            }
            msg2 = wsMessage(raw_message=click, app=app, ws=ws)
            sync2 = await ws.get_sync_template(message=msg2)
            ws.update_session(
                session_id=sid, template=sync2, window=msg2.window, route='/'
            )
            await ws.message_handler(message=msg2)
            await asyncio.sleep(0.4)

        asyncio.run(run())

        assert calls == ['ok']
        assert diffs and diffs[0].get('template')
        assert diffs[0]['template'] != {}
