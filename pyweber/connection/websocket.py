import gzip
import json
import inspect
import asyncio
import hashlib
import base64
import socket
import ssl
from uuid import uuid4
from typing import Callable, TYPE_CHECKING, Any, Literal, Union
from time import time

from pyweber.models.ws_message import wsMessage
from pyweber.utils.utils import PrintLine
from pyweber.connection.session import sessions, Session
from pyweber.models.template_diff import TemplateDiff
from pyweber.models.task_manager import TaskManager
from pyweber.core.events import EventConstrutor, EventBook

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
        'current_target_uuid',
        'template',
        'values',
        'event_data',
        'window_data',
        'window_response',
        'window_event',
        'sessionId',
        'file_content'
    ]

def event_is_running(message: wsMessage, task_manager: TaskManager) -> bool: # pragma: no cover
    """Check if event is running"""
    if message.session_id in task_manager.active_handlers_async:
        template = sessions.get_session(session_id=message.session_id).template
        event_id = template.getElement(by='uuid', value=message.target_uuid).events.__dict__.get(f'on{message.type}')

        if event_id in task_manager.active_handlers_async[message.session_id]:
            return True

    return False

class WebsocketUpgrade: # pragma: no cover
    def __init__(self, headers: bytes):
        self.headers = headers.decode('iso-8859-1')

    @property
    def websocket_guid(self) -> str: return '258EAFA5-E914-47DA-95CA-C5AB0DC85B11'

    @property
    def client_secret_key(self) -> str:
        for text in self.headers.splitlines():
            if 'sec-websocket-key' in text.lower():
                return text.split(':',1)[-1].strip()

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

class WebsocketServer: # pragma: no cover

    def __init__(self, client: Union[socket.socket, ssl.SSLSocket]):
        self.id = None
        self.client = client
        self.__all_message: bytes = b''
        self.__messages: list[bytes] = []

    def __iter__(self):
        return self

    async def __aiter__(self):
        while True:
            while not self.__messages:
                await asyncio.sleep(0.01)
            yield self.__messages.pop(0)

    def __next__(self):
        try:
            return self.__messages.pop(0)
        except IndexError:
            raise StopIteration

    async def __anext__(self):
        return self.__next__()

    async def send(self, message: bytes, opcode: int = 1):
        assert isinstance(message, bytes)
        frame = await self.frame_to_send(message, opcode)
        self.client.sendall(frame)

    async def close(self):
        try:
            self.client.close()
        except Exception:
            pass

    async def read_exact(self, length: int) -> bytes:
        if length == 0:
            return b''

        data = b''
        self.client.setblocking(False)
        while len(data) < length:
            try:
                chunk = self.client.recv(length - len(data))
                if not chunk:
                    raise ConnectionError(f'Connection {self.id} closed')
                data += chunk
            except (ssl.SSLWantReadError, BlockingIOError):
                await asyncio.sleep(0.01)
            except OSError as e:
                raise ConnectionError(f'Connection {self.id} closed: {e}')
        return data

    async def manage_connection(self, message_handler: Callable):
        last_ping = time()
        ping_interval = 30.0
        current_opcode = None
        is_coro = inspect.iscoroutinefunction(message_handler)
        timeout = 60 * 60

        try:
            while True:
                try:
                    opcode, message, fin = await asyncio.wait_for(
                        self.receive_frame(), timeout=timeout
                    )

                    if opcode is None:
                        break

                    if opcode != 0:
                        current_opcode = opcode

                    self.__all_message += message

                    if fin:
                        if current_opcode in [1, 2]:
                            decoded = (
                                self.__all_message.decode('utf-8')
                                if current_opcode == 1
                                else self.__all_message
                            )
                            self.__messages.append(decoded)

                            if is_coro:
                                asyncio.create_task(message_handler(self))
                            else:
                                message_handler(self)

                            self.__all_message = b''

                        elif current_opcode == 8:
                            break

                        elif current_opcode == 9:
                            await self.send(b'', opcode=9)

                        elif current_opcode == 10:
                            pass

                    if time() - last_ping >= ping_interval:
                        await self.send(b'', opcode=9)
                        last_ping = time()

                    await asyncio.sleep(0.01)

                except asyncio.TimeoutError:
                    PrintLine(f'Connection {self.id} timed out', level='WARNING')
                    break

                except (ConnectionError, ConnectionResetError):
                    break

        except Exception as e:
            PrintLine(f'Unknown websocket error: {e}', level='ERROR')
            raise e

        finally:
            await self.close()
            PrintLine(text=f'Connection {self.id} closed.')

    async def receive_frame(self):

        header = await self.read_exact(2)

        fin = (header[0] & 0x80) >> 7
        opcode = header[0] & 0x0F
        mask = (header[1] & 0x80) >> 7
        payload_len = header[1] & 0x7F

        if not mask:
            return None, None, None

        if payload_len == 126:
            extended_payload = await self.read_exact(2)
            payload_len = int.from_bytes(extended_payload, byteorder='big')

        elif payload_len == 127:
            extended_payload = await self.read_exact(8)
            payload_len = int.from_bytes(extended_payload, byteorder='big')

        masking_key = await self.read_exact(4)
        payload = await self.read_exact(payload_len)

        unmasked_payload = bytearray(payload_len)

        for i in range(payload_len):
            unmasked_payload[i] = payload[i] ^ masking_key[i % 4]

        return opcode, bytes(unmasked_payload), fin

    async def frame_to_send(self, message: bytes, opcode: int = 1):

        assert isinstance(message, bytes)

        if opcode == 1:
            try:
                message.decode('utf-8')
            except UnicodeDecodeError:
                opcode = 2

        payload_len = len(message)
        frame = bytearray()
        frame.append(0x80 | opcode)

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
        self.ws_connections: dict[str, Union[WebsocketServer, Callable[..., Any]]] = {}
        self._window_response_future: dict[str, asyncio.Future] = {}
        self._file_content_future: dict[str, asyncio.Future] = {}
        self.old_template: 'Template' = None
        self.app = app

    @property
    def window_response(self): return self.__window_response

    @window_response.setter
    def window_response(self, value: dict[str, Any]):
        assert isinstance(value, dict)
        self.__window_response = value

    def event_handler(self, message: wsMessage):
        return EventConstrutor(
            target_id=message.target_uuid,
            current_target_id=message.current_target_uuid,
            app=self.app,
            ws=self,
            session=sessions.get_session(session_id=message.session_id),
            route=message.route,
            event_data=message.event_data,
            event_type=message.type
        ).build_event()

    async def message_handler(self, message: wsMessage):

        event_handler = self.event_handler(message)

        if message.event_ref == 'document':
            if event_handler.current_target:
                event_id = event_handler.current_target.events.__dict__.get(f'on{message.type}')
                if event_id and event_id in EventBook:
                    handler: Callable[..., Any] = EventBook.get(event_id).get('event')

                    if inspect.iscoroutinefunction(handler):
                        if event_id not in self.task_manager.active_handlers_async.get(message.session_id, {}):
                            await self.task_manager.create_task_async(
                                session_id=message.session_id,
                                event_id=event_id,
                                handler=handler,
                                event_handler=event_handler
                            )
                    else:
                        if event_id not in self.task_manager.active_handlers.get(message.session_id, {}):
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
                # session.template = updated_template

                data['template'] = await self.get_template_diff(
                    session=session
                )

        return json.dumps(data, ensure_ascii=False, indent=4)

    async def __send(self, data: Any, handler: Callable):
        await handler(data)

    async def send_message(self, data, session_id, route=None):
        target_connections = {}

        if session_id:
            target_connections = {session_id: self.ws_connections.get(session_id)}
        else:
            if route:
                target_connections = {
                    i: conn for i, conn in self.ws_connections.items()
                    if sessions.get_session(i) and sessions.get_session(i).current_route == route
                }
            else:
                target_connections = dict(self.ws_connections)

        for s_id, handler in target_connections.items():
            if handler is None:
                continue
            try:
                json_data = await self.data_to_json(
                    data={key: value for key, value in data.items()},
                    session_id=s_id,
                )
                if self.protocol == 'uvicorn':
                    await self.__send({'type': 'websocket.send', 'text': json_data}, handler=handler)
                else:
                    await self.__send(json_data.encode('utf-8'), handler=handler.send)
            except Exception as e:
                PrintLine(text=f"Failed to send to session {s_id}: {e}", level='WARNING')

    # async def get_window_response(self, timeout: int):
    #     start_time = time.time()

    #     while time.time() - start_time < timeout:
    #         await asyncio.sleep(0.4)

    #         if self.window_response:
    #             break

    #     return self.window_response

    async def get_window_response(self, timeout: int, session_id: str):
        """Retorna window_response assim que estiver disponível ou timeout."""

        # Cria Future se não existir
        if session_id not in self._window_response_future:
            self._window_response_future[session_id] = asyncio.get_event_loop().create_future()

        try:
            # Espera pela resposta ou timeout
            result = await asyncio.wait_for(self._window_response_future[session_id], timeout)
            return result
        except asyncio.TimeoutError:
            # Timeout: retorna None ou valor atual
            return None
        finally:
            # Limpa a future para próxima chamada
            self._window_response_future.pop(session_id, None)

    async def set_window_response(self, response: dict, session_id: str):
        """Quando chega uma resposta do client, dispara a future."""
        self.window_response = response

        future = self._window_response_future.get(session_id)
        if future and not future.done():
            future.set_result(response)

    async def get_file_content(self, timeout: int, file_id: str):
        if file_id not in self._file_content_future:
            self._file_content_future[file_id] = asyncio.get_event_loop().create_future()
        try:
            result = await asyncio.wait_for(self._file_content_future[file_id], timeout)
            return result
        except asyncio.TimeoutError:
            return None
        finally:
            self._file_content_future.pop(file_id, None)

    async def set_file_content(self, response: dict, file_id: str):
        self.file_content = response

        future = self._file_content_future.get(file_id)

        if future and not future.done():
            future.set_result(response)

    async def get_template_diff(self, session: Session):

        diff = TemplateDiff()

        for tag in ['head', 'body']:
            diff.track_differences(
                new_element=session.template.querySelector(tag),
                old_element=session.old_template.querySelector(tag)
            )

        session.old_template = session.template.clone()

        return diff.differences

class WebsocketManager(BaseWebsockets): # pragma: no cover
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
        session = sessions.get_session(session_id=message.session_id)
        if session:
            session.old_template = sync_template.clone()
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
        sessions.remove_session(session_id=session_id)

        if session_id in self.ws_connections:
            del self.ws_connections[session_id]

        try:
            await self.task_manager.cancel_session_handlers(session_id=session_id)
            await self.task_manager.cancel_all_tasks_async(session_id=session_id)
        except TypeError:
            pass

    def process_ws_message_handler(self, message: Union[str, bytes]):
        try:
            if isinstance(message, bytes):
                message = gzip.decompress(message).decode('utf-8')

            message: dict[str, dict[str, str] | str] = json.loads(message)

            if not isinstance(message, dict):
                return {}

            if not all(key in need_message_keys() for key in message):
                return {}

            if not message.get('template') and message.get('window_data'):
                return {}

            route = message.get('route', '')
            route = route[:-1] if route.endswith('/') and len(route) > 1 else route
            if route not in self.app.list_routes:
                return {}

            return message
        except Exception as e:
            PrintLine(text=f'Error to decode websocket message handler {e}', level='ERROR')
            return {}

    async def ws_handler_wsgi(self, ws_server: WebsocketServer):
        for message in ws_server:
            raw_message = self.process_ws_message_handler(message=message)

            if not raw_message:
                continue

            message = wsMessage(raw_message=raw_message, app=self.app, ws=self)

            if message.file_content:
                await self.set_file_content(message.file_content, message.file_content.get('file_id'))

            if message.window_response:
                await self.set_window_response(message.window_response, message.session_id)

            sync_template = await self.get_sync_template(message=message)

            if not message.session_id or any(
                session_id not in sessions.all_sessions
                for session_id in [message.session_id, ws_server.id]
            ):
                ws_server.id = self.get_session_id(session_id=message.session_id)
                self.ws_connections[ws_server.id] = ws_server

                self.add_session(
                    session_id=ws_server.id,
                    template=sync_template,
                    window=message.window,
                    route=message.route
                )

                await self.send_message(
                    data={
                        'setSessionId': ws_server.id,
                        'windowEvents': message.window.get_all_event_ids
                    },
                    session_id=ws_server.id
                )

            if message.type and message.event_ref and not event_is_running(
                message=message, task_manager=self.task_manager
            ):
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
                            message = wsMessage(raw_message=raw_message, app=self.app, ws=self)

                            if message.window_response:
                                await self.set_window_response(message.window_response, message.session_id)

                            if message.file_content:
                                await self.set_file_content(message.file_content, message.session_id)

                            sync_template = await self.get_sync_template(message=message)

                            if not message.session_id or message.session_id not in sessions.all_sessions:
                                ws_connection = self.get_session_id(session_id=message.session_id)

                                self.add_session(
                                    session_id=ws_connection,
                                    template=sync_template,
                                    window=message.window,
                                    route=message.route
                                )

                                self.ws_connections[ws_connection] = send

                                await self.send_message(
                                    data={
                                        'setSessionId': ws_connection,
                                        'windowEvents': message.window.get_all_event_ids,
                                    },
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

        finally:
            await self.clear_session(session_id=ws_connection)

    async def connect_wsgi(self, ws_connection: WebsocketServer):
        await ws_connection.manage_connection(self.ws_handler_wsgi)
        await self.clear_session(session_id=ws_connection.id)

    async def __call__(self, scope, receive, send):
        assert scope.get('type', None) == 'websocket'
        await self.ws_handler_asgi(receive=receive, send=send)

        for id, handler in self.ws_connections.items():
            if handler == send:
                sessions.remove_session(session_id=id)
                del self.ws_connections[id]
                break
