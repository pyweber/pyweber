import json
import inspect
import asyncio
import time
import hashlib
import base64
import socket
from uuid import uuid4
from typing import Callable, TYPE_CHECKING, Any, Literal, Union

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

def event_is_running(message: wsMessage, task_manager: TaskManager) -> bool: # pragma: no cover
    """Check if event is running"""
    if message.session_id in task_manager.active_handlers_async:
        template = sessions.get_session(session_id=message.session_id).template
        event_id = template.getElement(by='uuid', value=message.target_uuid).events.__dict__.get(f'on{message.type}')

        if event_id in task_manager.active_handlers_async[message.session_id]:
            return True
    
    return False

class WebsocketUpgrade:
    def __init__(self, headers: bytes):
        self.headers = headers.decode('iso-8859-1')

    @property
    def websocket_guid(self) -> str: return '258EAFA5-E914-47DA-95CA-C5AB0DC85B11'

    @property
    def client_secret_key(self) -> str:
        for text in self.headers.splitlines():
            if 'Sec-WebSocket-Key:' in text:
                return text.split(':')[-1].strip()
    
    @property
    def server_accept_key(self):
        sha_1_hash = hashlib.sha1(
            string=(self.client_secret_key+self.websocket_guid).encode('utf-8')
        ).digest()

        return base64.b64encode(sha_1_hash).decode('utf-8')
    
    @property
    def upgrade_response(self):
        return (
            'HTTP/1.1 101 Switching Protocols\r\n'
            'Upgrade: websocket\r\n'
            'Connection: Upgrade\r\n'
            f'Sec-WebSocket-Accept: {self.server_accept_key}\r\n\r\n'
        )

class WebsocketServer:
    def __init__(self, connection: socket.socket):
        self.id = str(uuid4())
        self.__connection = connection
        self.__all_message: bytes = b''
        self.__messages: list[str | bytes] = []
    
    def __iter__(self):
        return self
    
    async def __aiter__(self):
        return self.__iter__()
    
    def __next__(self):
        try:
            message = [self.__messages[0]]
            self.__messages.pop(0)
            return message[-1]
        except IndexError:
            raise StopIteration
    
    async def __anext__(self):
        return self.__next__()
    
    @property
    def connection(self): return self.__connection

    async def send(self, message: bytes):
        assert isinstance(message, bytes)
        self.connection.sendall(await self.frame_to_send(message))
    
    def close(self):
        self.__connection.close()
    
    def read_frames(self, length: int):
        data = b''

        while len(data) < length:
            chunk = self.connection.recv(length - len(data))

            if not chunk:
                raise ConnectionError(f'Connetion {self.id} closed')
            
            data += chunk
        
        return data
    
    async def manage_connection(self, message_handler: Callable):
        try:
            time = 0

            while True:
                opcode, message = await self.receive_frame()

                if opcode is None:
                    break

                if opcode == 0:
                    self.__all_message += message

                elif opcode in [1,2]:
                    self.__all_message += message
                    message = self.__all_message.decode('utf-8') if opcode == 1 else self.__all_message
                    
                    self.__messages.append(message)
                    
                    if inspect.iscoroutinefunction(message_handler):
                        await message_handler(self)
                    else:
                        message_handler(self)

                    self.__all_message = b''
                
                elif opcode == 8:
                    break

                elif opcode == 10:
                    pass
                
                elif opcode == 9:
                    self.connection.sendall(await self.frame_to_send(b'', opcode=10))

                else:
                    PrintLine(f'Unknown websocket Error', level='ERROR')
                
                if time > 30:
                    time = 0
                    self.connection.sendall(await self.frame_to_send(b'', opcode=9))
                
                time += 0.01
                await asyncio.sleep(0.01)
        
        except ConnectionError as e:
            PrintLine(f'Connection error with {self.id}: {e}')
        except Exception as e:
            PrintLine(f'Unknown websocket error: {e}', level='ERROR')
            raise e
        finally:
            self.close()
            PrintLine(text=f'Connection {self.id} closed.')
    
    async def receive_frame(self):
        header = self.read_frames(2)

        if not header:
            return None, None
        
        opcode = header[0] & 0x0F
        mask = (header[1] & 0x80) >> 7
        payload_len = header[1] & 0x7F

        if not mask:
            return None, None
        
        if payload_len == 126:
            extended_payload = self.read_frames(2)
            payload_len = int.from_bytes(extended_payload, byteorder='big')
        elif payload_len == 127:
            extended_payload = self.read_frames(8)
            payload_len = int.from_bytes(extended_payload, byteorder='big')
        
        masking_key = self.read_frames(4)
        payload = self.read_frames(payload_len)
        unmasked_payload = bytearray(payload_len)

        for i in range(payload_len):
            unmasked_payload[i] = payload[i] ^ masking_key[i % 4]
        
        return opcode, bytes(unmasked_payload)
    
    async def frame_to_send(self, message: bytes, opcode: int = 1):
        assert isinstance(message, bytes)

        if opcode == 1:
            try:
                message.decode('utf-8')
            except UnicodeDecodeError:
                opcode = 2
        
        payload_len = len(message)
        frame = [0x80 | opcode]

        if payload_len <= 125:
            frame.append(payload_len)
        elif payload_len <= 65535:
            frame.append(126)
            frame.extend(payload_len.to_bytes(2, byteorder='big'))
        else:
            frame.append(127)
            frame.extend(payload_len.to_bytes(8, byteorder='big'))
        
        frame.extend(message)

        return bytes(frame)

class BaseWebsockets: # pragma: no cover
    def __init__(self, app: 'Pyweber', protocol: Literal['pyweber', 'uvicorn'] = 'pyweber'):
        self.protocol: Literal['pyweber', 'uvicorn'] = protocol
        self.task_manager = TaskManager()
        self.ws_connections: dict[str, WebsocketServer | Callable[..., Any]] = {}
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
    
    async def data_to_json(self, data: Any, session_id: str, last_target: bool = False):
        if isinstance(data, dict):
            session = sessions.get_session(session_id=session_id)
            current_template: 'Template' = data.get('template', None)

            if current_template:
                updated_template = current_template.clone()

                data['template'] = await self.get_template_diff(
                    session_template=current_template,
                    old_template=None
                )

                session.template = updated_template

                if last_target:
                    self.old_template = updated_template

        return json.dumps(data, ensure_ascii=False, indent=4)

    async def __send(self, data: Any, handler: Callable):
        await handler(data)

    async def send_message(self, data: dict[str, Union[str, 'Template']], session_id: str, route: str = None):

        target_connections: dict[str, Callable | WebsocketServer] = {}

        if session_id:
            target_connections = {session_id: self.ws_connections[session_id]}
        else:
            if route:
                target_connections = {}

                for i, conn in self.ws_connections.items():
                    if sessions.get_session(i).current_route == route:
                        target_connections[i] = conn
            else:
                target_connections = {i: conn for i, conn in self.ws_connections.items()}
        
        total_target = len(target_connections)
        counter = 0

        try:
            if self.protocol == 'uvicorn':
                
                for s_id, handler in target_connections.items():
                    counter += 1
                    json_data = await self.data_to_json(
                        data={key: value for key, value in data.items()},
                        session_id=s_id,
                        last_target=(total_target==counter)
                    )

                    await self.__send(
                        {'type': 'websocket.send', 'text': json_data},
                        handler=handler
                    )
            else:
                for s_id, handler in target_connections.items():
                    counter += 1

                    json_data = await self.data_to_json(
                        data={key: value for key, value in data.items()},
                        session_id=s_id,
                        last_target=(total_target==counter)
                    )

                    await self.__send(
                        json_data.encode('utf-8'),
                        handler=handler.send
                    )

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
    
    async def get_template_diff(self, session_template: 'Template', old_template: 'Template' = None):
        old_template = old_template if old_template else self.old_template

        diff = TemplateDiff()
        
        for tag in ['head', 'body']:
            old_element = self.old_template.querySelector(tag)

            diff.track_differences(
                new_element=session_template.querySelector(tag),
                old_element=old_element
            )
        
        return diff.differences

class WebsocketManager(BaseWebsockets):
    def __init__(self, app: 'Pyweber', protocol: Literal['uvicorn', 'pyweber'] = 'pyweber'):
        super().__init__(app=app, protocol=protocol)
    
    def add_connection(self, connection: WebsocketServer):
        assert isinstance(connection, WebsocketServer)
        self.ws_connections[connection.id] = connection
    
    def remove_connection(self, id: str):
        if id in self.ws_connections:
            self.ws_connections[id].close()
            del self.ws_connections[id]
    
    def remove_all(self):
        for id, conn in self.ws_connections.items():
            conn.close()
            del self.ws_connections[id]
    
    def send_all(self, message: bytes):
        for _, conn in self.ws_connections.items():
            conn.send(message=message)
    
    def get_connection(self, id: str):
        return self.ws_connections.get(id, None)
    
    def update_app_template(self, new_template: 'Template', route: str):
        if route in self.app.list_routes:
            group, route = self.app.get_group_and_route(route=route)
            self.app.update_route(route=route, group=group, template=new_template)
    
    def get_session_id(self, session_id: str = None):
        return session_id or str(uuid4())
    
    async def get_sync_template(self, message: wsMessage):
        assert isinstance(message, wsMessage)
        sync_template = await message.template
        self.old_template = sync_template.clone()
        return sync_template
    
    def update_app_template(self, new_template: 'Template', route: str):
        if route in self.app.list_routes:
            group, route = self.app.get_group_and_route(route=route)
            self.app.update_route(route=route, group=group, template=new_template)
    
    def add_session(self, session_id: str, template: 'Template', window: 'Window', route: str):
        sessions.add_session(
            session_id=session_id,
            session=Session(
                template=template,
                window=window,
                session_id=session_id,
                current_route=route
            )
        )
    
    def update_session(self, session_id: str, template: 'Template', window: 'Window', route: str):
        session = sessions.get_session(session_id=session_id)
        session.template = template
        session.window = window
        session.current_route = route
    
    async def clear_session(self, session_id: str):
        await self.task_manager.cancel_session_handlers(session_id=session_id)
        await self.task_manager.cancel_all_tasks_async(session_id=session_id)
        sessions.remove_session(session_id=session_id)

        if session_id in self.ws_connections:
            del self.ws_connections[session_id]
    
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
    
    async def ws_handler_wsgi(self, ws_server: WebsocketServer):
        for message in ws_server:
            raw_message = self.process_ws_message_handler(message=message)

            if raw_message:
                message = wsMessage(raw_message=raw_message, app=self.app, ws=self)

                sync_template = await self.get_sync_template(message=message)

                if not message.session_id or any(session_id not in sessions.all_sessions for session_id in [message.session_id, ws_server.id]):
                    ws_server.id = self.get_session_id(session_id=message.session_id)
                    self.ws_connections[ws_server.id] = ws_server

                    self.add_session(
                        session_id=ws_server.id,
                        template=sync_template,
                        window=message.window,
                        route=message.route
                    )

                    await self.send_message(
                        data={'setSessionId': ws_server.id, 'window': message.window.get_all_event_ids},
                        session_id=ws_server.id
                    )
                
                if message.type and message.event_ref and not event_is_running(message=message, task_manager=self.task_manager):
                    self.update_session(
                        session_id=ws_server.id,
                        template=sync_template,
                        window=message.window,
                        route=message.route
                    )

                    await self.message_handler(message=message)
    
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
                                self.add_session(session_id=ws_connection, template=sync_template, window=message.window, route=message.route)

                                self.ws_connections[ws_connection] = send

                                await self.send_message(
                                    data={'setSessionId': ws_connection},
                                    session_id=ws_connection
                                )
                            
                            if message.type and message.event_ref and not event_is_running(message=message, task_manager=self.task_manager):
                                self.update_session(
                                    session_id=ws_connection,
                                    template=sync_template,
                                    window=message.window,
                                    route=message.route
                                )

                                await self.message_handler(message=message)
                else:
                    break

        except Exception as e:
            PrintLine(text=f'Websocket server error: {e}', level='ERROR')
            raise e
        
        # finally:
        #     await self.clear_session(session_id=ws_connection)
    
    async def connect_wsgi(self, ws_connection: WebsocketServer):
        PrintLine(text=f'Connected websocket with id: {ws_connection.id}')
        await ws_connection.manage_connection(self.ws_handler_wsgi)
        sessions.remove_session(session_id=ws_connection.id)
        self.remove_connection(id=ws_connection.id)
    
    async def __call__(self, scope, receive, send):
        assert scope.get('type', None) == 'websocket'
        await self.ws_handler_asgi(receive=receive, send=send)

        for id, handler in self.ws_connections.items():
            if handler == send:
                sessions.remove_session(session_id=id)
                del self.ws_connections[id]
                break