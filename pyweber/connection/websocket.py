import json
import inspect
import asyncio
import ssl
import time
from uuid import uuid4
import websockets as ws
from typing import Callable, TYPE_CHECKING, Any, Literal, Union
from websockets.asyncio.server import serve as async_serve

from pyweber.models.ws_message import wsMessage
from pyweber.utils.utils import PrintLine
from pyweber.connection.session import sessions, Session
from pyweber.models.template_diff import TemplateDiff
from pyweber.models.task_manager import TaskManager

if TYPE_CHECKING: # pragma: no cover
    from pyweber.pyweber.pyweber import Pyweber
    from pyweber.core.template import Template
    from pyweber.core.window import Window

def need_message_keys(): # pragma: no cover
    return [
        'type',
        'event_ref',
        'route',
        'target_uuid',
        'template',
        'values',
        'event_data',
        'window_data',
        'window_response',
        'window_event',
        'sessionId'
    ]

class BaseWebsockets: # pragma: no cover
    def __init__(self, app: 'Pyweber', protocol: Literal['pyweber', 'uvicorn'] = 'pyweber'):
        self.protocol: Literal['pyweber', 'uvicorn'] = protocol
        self.task_manager = TaskManager()
        self.ws_connections: dict[str, Callable] = {}
        self.window_response: dict[str, Any] = {}
        self.old_template: 'Template' = None
        self.app = app
    
    async def message_handler(self, message: wsMessage):
        from pyweber.core.events import EventConstrutor, EventBook

        event_handler = EventConstrutor(
            target_id=message.target_uuid,
            app=self.app,
            ws=self,
            session=sessions.get_session(session_id=message.session_id),
            route=message.route,
            event_data=message.event_data,
            event_type=message.type
        ).build_event()

        if message.event_ref == 'document':
            if event_handler.element:
                event_id = event_handler.element.events.__dict__.get(f'on{message.type}')
                if event_id and event_id in EventBook:
                    handler = EventBook.get(event_id)

                    if inspect.iscoroutinefunction(handler):
                        if event_id not in self.task_manager.active_handlers_async.get(message.session_id, {}):
                            await self.task_manager.create_task_async(
                                session_id=message.session_id,
                                event_id=event_id,
                                handler=handler,
                                event_handler=event_handler
                            )
                    else:
                        self.task_manager.create_task(
                            session_id=message.session_id,
                            event_id=event_id,
                            handler=handler,
                            event_handler=event_handler
                        )
        
        elif message.event_ref == 'window':
            handler = message.window.get_event(event_id=message.window_event)
            event_id = f'{message.window_event}_{message.session_id}'
            if callable(handler):
                if inspect.iscoroutinefunction(handler):
                    await self.task_manager.create_task_async(
                        session_id=message.session_id,
                        event_id=event_id,
                        handler=handler,
                        event_handler=event_handler
                    )
                else:
                    self.task_manager.create_task(
                        session_id=message.session_id,
                        event_id=event_id,
                        handler=handler,
                        event_handler=event_handler
                    )
        

    async def send_message(self, data: dict[str, Union[str, 'Template']], session_id: str, route: str = None):
        
        if data.get('template', None) and route:
            data['template'] = await self.get_template_diff(
                session_template=data['template'],
                route=route
            )

        try:
            json_data = json.dumps(data, ensure_ascii=False, indent=4)

            send = self.ws_connections.get(session_id, None)
            group_senders = {session_id: send} if send else self.ws_connections

            for _, handler in group_senders.items():
                if self.protocol == 'uvicorn':
                    await handler({'type': 'websocket.send', 'text': json_data})
                else:
                    await handler(json_data)

        except Exception as e:
            PrintLine(text=f"Websocket server error {e}", level='ERROR')
            raise e
    
    async def get_window_response(self, timeout: int):
        start_time = time.time()

        while time.time() - start_time < timeout:
            await asyncio.sleep(0.1)

            if self.window_response:
                break
        
        return self.window_response
    
    async def get_template_diff(self, session_template: 'Template', route: str):
        diff = TemplateDiff()

        for tag in ['head', 'body']:
            old_element = self.old_template.querySelector(tag)

            diff.track_differences(
                new_element=session_template.querySelector(tag),
                old_element=old_element
            )
        
        self.old_template = session_template.clone()
        
        return diff.differences

class WebSocket(BaseWebsockets): # pragma: no cover
    def __init__(self, app: 'Pyweber', protocol: Literal['pyweber', 'uvicorn'] = 'pyweber'):
        super().__init__(app=app, protocol=protocol)
    
    def update_app_template(self, new_template: 'Template', route: str):
        if route in self.app.list_routes:
            group, route = self.app.get_group_and_route(route=route)
            self.app.update_route(route=route, group=group, template=new_template)
    
    def add_session(self, session_id: str, template: 'Template', window: 'Window'):
        sessions.add_session(
            session_id=session_id,
            session=Session(
                template=template,
                window=window,
                session_id=session_id
            )
        )
    
    def get_session_id(self, session_id: str = None):
        return session_id or str(uuid4())
    
    async def get_sync_template(self, message: wsMessage):
        assert isinstance(message, wsMessage)
        sync_template = await message.template
        self.old_template = sync_template.clone()
        return sync_template
    
    def update_session(self, session_id: str, template: 'Template', window: 'Window'):
        session = sessions.get_session(session_id=session_id)
        session.template = template
        session.window = window
    
    def process_ws_message_handler(self, message: str):
        try:
            message: dict[str, dict[str, str] | str] = json.loads(message)

            if not isinstance(message, dict):
                return {}
            
            if not all(key in need_message_keys() for key in message):
                return {}
            
            if not message.get('template') and message.get('window_data'):
                return {}
            
            if message.get('route') not in self.app.list_routes:
                return {}
            
            return message
        except Exception as e:
            PrintLine(text=f'Error to decode websocket message handler {e}', level='ERROR')
            return {}
    
    async def clear_session(self, session_id: str):
        await self.task_manager.cancel_session_handlers(session_id=session_id)
        await self.task_manager.cancel_all_tasks_async(session_id=session_id)
        sessions.remove_session(session_id=session_id)

        if session_id in self.ws_connections:
            del self.ws_connections[session_id]
    
    async def ws_handler_wsgi(self, ws_connection: ws.server.ServerConnection):
        try:
            async for message in ws_connection:
                raw_message = self.process_ws_message_handler(message=message)

                if raw_message:
                    message = wsMessage(raw_message=raw_message, app=self.app, ws=self)
                    self.window_response = message.window_response
                    sync_template = await self.get_sync_template(message=message)

                    if not message.session_id or message.session_id not in sessions.all_sessions:
                        ws_connection.id = self.get_session_id(session_id=message.session_id)
                        self.add_session(session_id=ws_connection.id, template=sync_template, window=message.window)
                        
                        self.ws_connections[ws_connection.id] = ws_connection.send
                        await self.send_message(
                            data={'setSessionId': ws_connection.id, 'window': message.window.get_all_event_ids},
                            session_id=ws_connection.id
                        )
                    
                    if message.type and message.event_ref and not event_is_running(message=message, task_manager=self.task_manager):
                        self.update_session(
                            session_id=ws_connection.id,
                            template=sync_template,
                            window=message.window
                        )

                        await self.message_handler(message=message)
        
        except ws.ConnectionClosedError as e:
            PrintLine(f'Websocket connection was lost: {e}', level='ERROR')

        except Exception as e:
            PrintLine(f'Websocket server error: {e}', level='ERROR')
            raise e

        finally:
            await self.clear_session(session_id=str(ws_connection.id))
    
    async def ws_handler_asgi(self, receive: Callable, send: Callable):
        ws_connection: str = None

        try:
            while True:
                raw_message = await receive()

                if raw_message.get('type') == 'websocket.connect':
                    await send({'type': 'websocket.accept'})
                elif raw_message.get('type') == 'websocket.receive':
                    text = raw_message.get('text', None)

                    if text:
                        raw_message = self.process_ws_message_handler(message=text)

                        if raw_message:
                            message = wsMessage(raw_message=json.loads(text), app=self.app, ws=self)
                            self.window_response = message.window_response
                            sync_template = await self.get_sync_template(message=message)

                            if not message.session_id or message.session_id not in sessions.all_sessions:
                                ws_connection = self.get_session_id(session_id=message.session_id)
                                self.add_session(session_id=ws_connection, template=sync_template, window=message.window)

                                self.ws_connections[ws_connection] = send

                                await self.send_message(
                                    data={'setSessionId': ws_connection},
                                    session_id=ws_connection
                                )
                            
                            if message.type and message.event_ref and not event_is_running(message=message, task_manager=self.task_manager):
                                self.update_session(
                                    session_id=ws_connection,
                                    template=sync_template,
                                    window=message.window
                                )

                                await self.message_handler(message=message)
                else:
                    break

        except Exception as e:
            PrintLine(text=f'Websocket server error: {e}', level='ERROR')
            raise e
        
        finally:
            await self.clear_session(session_id=ws_connection)
    
    async def ws_start(self, host: str, port: str, cert_file: str, key_file: str):
        ssl_context = None

        def ssl_setup():
            try:
                ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
                ssl_context.load_cert_chain(certfile=cert_file, keyfile=key_file)
            except Exception as e:
                raise e
            return ssl_context
        
        try:
            if cert_file and key_file:
                ssl_context = ssl_setup()

            async with async_serve(self.ws_handler_wsgi, host=host, port=port, ssl=ssl_context, max_size=2**48, write_limit=2**48) as server:
                await server.serve_forever()

        except Exception as e:
            raise e
    
    async def __call__(self, scope, receive, send):
        assert scope.get('type', None) == 'websocket'
        await self.ws_handler_asgi(receive=receive, send=send)

def event_is_running(message: wsMessage, task_manager: TaskManager) -> bool: # pragma: no cover
    """Check if event is running"""
    if message.session_id in task_manager.active_handlers_async:
        template = sessions.get_session(session_id=message.session_id).template
        event_id = template.getElement(by='uuid', value=message.target_uuid).events.__dict__.get(f'on{message.type}')

        if event_id in task_manager.active_handlers_async[message.session_id]:
            return True
    
    return False