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
from pyweber.utils.security import (
    SESSION_COOKIE_NAME,
    generate_session_id,
    unsign_value,
)
from pyweber.connection.session import sessions, Session
from pyweber.models.template_diff import TemplateDiff
from pyweber.models.task_manager import TaskManager
from pyweber.core.events import EventConstrutor
from pyweber.models.context import set_current_window, reset_current_window

if TYPE_CHECKING:
    from pyweber.pyweber.pyweber import Pyweber
    from pyweber.core.template import Template
    from pyweber.core.window import Window

def need_message_keys():
    """Keys the browser always includes in ``getEventData`` payloads."""
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
        'file_content',
        'handoffToken',
    ]


def _ws_message_is_actionable(message: dict) -> bool:
    """True when the payload can create a session or drive an event/update.

    The old gate rejected *any* message without ``template`` when the session
    was unknown — that dropped clicks, window responses, and handshakes that
    omit outerHTML (``includeTemplate: false``).
    """
    if message.get('template'):
        return True
    if message.get('handoffToken'):
        return True
    if message.get('type') and message.get('event_ref'):
        return True
    if message.get('window_response'):
        return True
    if message.get('file_content'):
        return True
    session_id = message.get('sessionId')
    return bool(session_id and session_id in sessions.all_sessions)

def event_is_running(message: wsMessage, task_manager: TaskManager) -> bool:
    """Check if event is running"""
    if message.session_id in task_manager.active_handlers_async:
        template = sessions.get_session(session_id=message.session_id).template
        element = template.getElement(by='uuid', value=message.target_uuid)
        handler = element.events.__dict__.get(f'on{message.type}') if element else None

        if not callable(handler):
            return False

        event_id = f'event_{id(handler)}'

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

class WebsocketServer:

    def __init__(self, client: Union[socket.socket, ssl.SSLSocket], cookies: dict[str, str] | None = None):
        self.id = None
        self.client = client
        self.cookies = cookies or {}
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
        consumer_task: asyncio.Task | None = None

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
                            self.__all_message = b''

                            # One long-lived consumer (async for). Spawning a
                            # task per frame made sync ``for`` exit after the
                            # first drain and raced multiple consumers.
                            if consumer_task is None or consumer_task.done():
                                if is_coro:
                                    consumer_task = asyncio.create_task(
                                        message_handler(self)
                                    )
                                else:
                                    message_handler(self)

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
            if consumer_task is not None and not consumer_task.done():
                consumer_task.cancel()
                try:
                    await consumer_task
                except (asyncio.CancelledError, Exception):
                    pass
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

class BaseWebsockets:
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
        session = sessions.get_session(session_id=message.session_id)
        return EventConstrutor(
            target_id=message.target_uuid,
            current_target_id=message.current_target_uuid,
            app=self.app,
            ws=self,
            session=session,
            route=message.route,
            event_data=message.event_data,
            event_type=message.type
        ).build_event()

    async def message_handler(self, message: wsMessage):
        token = set_current_window(message.window)
        try:
            if sessions.get_session(session_id=message.session_id) is None:
                return

            event_handler = self.event_handler(message)

            if message.event_ref == 'document':
                if event_handler.current_target:
                    raw = event_handler.current_target.events.__dict__.get(f'on{message.type}')
                    handler: Callable[..., Any] | None = None
                    event_id: str | None = None

                    if callable(raw):
                        handler = raw
                        event_id = f'event_{id(handler)}'
                    elif isinstance(raw, str):
                        from pyweber.core.events import EventBook
                        entry = EventBook.get(raw)
                        if entry and callable(entry.get('event')):
                            handler = entry['event']
                            event_id = raw

                    if handler and event_id:
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
        finally:
            reset_current_window(token)

    async def data_to_json(self, data: Any, session_id: str, last_target: bool = False):
        if isinstance(data, dict):
            session = sessions.get_session(session_id=session_id)
            current_template: 'Template' = data.get('template', None)

            if current_template and session is not None:
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
        """When a client window_response arrives, resolve confirm/prompt or run timers."""
        if self._is_timer_response(response):
            await self._dispatch_timer_callback(response, session_id)
            return

        self.window_response = response

        future = self._window_response_future.get(session_id)
        if future and not future.done():
            future.set_result(response)

    @staticmethod
    def _is_timer_response(response: dict | None) -> bool:
        if not isinstance(response, dict):
            return False
        return bool(
            response.get('timeout_completed')
            or response.get('interval_executed')
            or response.get('animation_frame_executed')
        )

    async def _dispatch_timer_callback(self, response: dict, session_id: str):
        session = sessions.get_session(session_id=session_id)
        window = getattr(session, 'window', None) if session else None
        if window is None:
            return

        timer_id = (
            response.get('timeout_id')
            or response.get('interval_id')
            or response.get('frame_id')
        )
        if not timer_id:
            return

        keep = bool(response.get('interval_executed')) and window.is_interval_id(timer_id)
        callback = window.take_timer_callback(timer_id, keep=keep)
        if not callable(callback):
            return

        token = set_current_window(window)
        try:
            if inspect.iscoroutinefunction(callback):
                await callback()
            else:
                callback()
        finally:
            reset_current_window(token)

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

        if session.old_template is None:
            try:
                session.old_template = session.template.clone()
            except Exception:
                # No baseline → empty diff rather than crashing the WS send path
                return {}

        for tag in ['head', 'body']:
            old_el = session.old_template.querySelector(tag)
            new_el = session.template.querySelector(tag)
            if old_el is None or new_el is None:
                continue
            diff.track_differences(
                new_element=new_el,
                old_element=old_el,
            )

        try:
            session.old_template = session.template.clone()
        except Exception as exc:
            PrintLine(text=f'template clone after diff failed: {exc}', level='ERROR')

        return diff.differences

class WebsocketManager(BaseWebsockets):
    def __init__(self, app: 'Pyweber', protocol: Literal['uvicorn', 'pyweber'] = 'pyweber'):
        super().__init__(app=app, protocol=protocol)

    def add_connection(self, connection: WebsocketServer):
        assert isinstance(connection, WebsocketServer)
        self.ws_connections[connection.id] = connection

    def remove_connection(self, id: str):
        conn = self.ws_connections.pop(id, None)
        if conn is None:
            return
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(conn.close())
        except RuntimeError:
            try:
                conn.client.close()
            except Exception:
                pass

    def remove_all(self):
        ids = list(self.ws_connections.keys())
        for conn_id in ids:
            self.remove_connection(conn_id)

    def send_all(self, message: bytes):
        for conn in list(self.ws_connections.values()):
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(conn.send(message=message))
            except RuntimeError:
                try:
                    asyncio.run(conn.send(message=message))
                except Exception:
                    pass

    def get_connection(self, id: str):
        return self.ws_connections.get(id, None)

    def update_app_template(self, new_template: 'Template', route: str):
        if route in self.app.list_routes:
            group, route = self.app.get_group_and_route(route=route)
            self.app.update_route(route=route, group=group, template=new_template)

    def get_session_id(self, session_id: str = None, cookies: dict[str, str] | None = None):
        """Resolve session id from signed HttpOnly cookie; never trust client id alone."""
        cookie_jar = cookies or {}
        signed = cookie_jar.get(SESSION_COOKIE_NAME)
        cookie_sid = unsign_value(signed) if signed else None
        if cookie_sid:
            return cookie_sid
        # Ignore client-supplied session_id when cookie is missing/invalid
        return generate_session_id()

    def bind_session_id(
        self,
        *,
        client_session_id: str | None,
        connection_id: str | None,
        cookies: dict[str, str] | None,
    ) -> tuple[str, bool]:
        """Resolve the session for this WS connection.

        Prefer an id already bound on the socket (``connection_id``). That stops
        the handshake race where a second frame still has ``sessionId: null`` and
        would otherwise mint a new session + ``clone_template`` (new UUIDs → no
        event handlers match the DOM).

        Returns ``(session_id, is_new)``.
        """
        if connection_id and connection_id in sessions.all_sessions:
            return connection_id, False

        if client_session_id and client_session_id in sessions.all_sessions:
            return client_session_id, False

        resolved = self.get_session_id(
            session_id=client_session_id,
            cookies=cookies or {},
        )
        if resolved in sessions.all_sessions:
            return resolved, False

        # Keep a stable id for this socket even before add_session runs
        if connection_id:
            return connection_id, True

        return resolved, True

    async def _ensure_session_and_template(
        self,
        message: wsMessage,
        *,
        connection_id: str | None,
        cookies: dict[str, str] | None,
        send_target,
    ) -> tuple[str, 'Template', bool]:
        """Bind session id *before* template sync, then create/reuse session."""
        session_id, is_new = self.bind_session_id(
            client_session_id=message.session_id,
            connection_id=connection_id,
            cookies=cookies,
        )
        message.session_id = session_id

        sync_template = await self.get_sync_template(message=message)

        if is_new:
            self.add_session(
                session_id=session_id,
                template=sync_template,
                window=message.window,
                route=message.route,
            )
            self.ws_connections[session_id] = send_target
            await self.send_message(
                data={
                    'setSessionId': session_id,
                    'windowEvents': message.window.get_all_event_ids,
                },
                session_id=session_id,
            )
        else:
            self.ws_connections[session_id] = send_target
            if message.get_value(key='template'):
                self.update_session(
                    session_id=session_id,
                    template=sync_template,
                    window=message.window,
                    route=message.route,
                )
                session = sessions.get_session(session_id=session_id)
                if session:
                    try:
                        session.old_template = sync_template.clone()
                    except Exception as exc:
                        PrintLine(
                            text=f'template clone for diff failed: {exc}',
                            level='ERROR',
                        )

        return session_id, sync_template, is_new

    async def get_sync_template(self, message: wsMessage):
        assert isinstance(message, wsMessage)
        sync_template = await message.template
        session = sessions.get_session(session_id=message.session_id)
        if session:
            try:
                session.old_template = sync_template.clone()
            except Exception as exc:
                # Never drop the WS event path because old_template clone failed
                # (historically Form/Input attrs setters broke Element.clone).
                PrintLine(text=f'template clone for diff failed: {exc}', level='ERROR')
                # Do not alias template (that yields empty diffs after mutations).
                if session.old_template is sync_template:
                    session.old_template = None
        return sync_template

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
            conn = self.ws_connections.pop(session_id)
            try:
                await conn.close()
            except Exception:
                try:
                    conn.client.close()
                except Exception:
                    pass

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

            # Require the JS contract keys (values may be null). Extra keys are
            # ignored — do not invert this into an allowlist over message.keys()
            # (that rejects nothing useful and confuses debugging).
            required = need_message_keys()
            if not all(key in message for key in required):
                return {}

            if not _ws_message_is_actionable(message):
                return {}

            route = message.get('route', '') or ''
            route = route[:-1] if route.endswith('/') and len(route) > 1 else route
            message['route'] = route
            if route not in self.app.list_routes:
                return {}

            return message
        except Exception as e:
            PrintLine(text=f'Error to decode websocket message handler {e}', level='ERROR')
            return {}

    async def ws_handler_wsgi(self, ws_server: WebsocketServer):
        async for message in ws_server:
            raw_message = self.process_ws_message_handler(message=message)

            if not raw_message:
                continue

            message = wsMessage(raw_message=raw_message, app=self.app, ws=self)

            if message.file_content:
                await self.set_file_content(message.file_content, message.file_content.get('file_id'))

            if message.window_response:
                await self.set_window_response(message.window_response, message.session_id)

            session_id, sync_template, _is_new = await self._ensure_session_and_template(
                message,
                connection_id=ws_server.id,
                cookies=getattr(ws_server, 'cookies', {}) or {},
                send_target=ws_server,
            )
            ws_server.id = session_id

            if message.type and message.event_ref and not event_is_running(
                message=message, task_manager=self.task_manager
            ):
                self.update_session(
                    session_id=session_id,
                    template=sync_template,
                    window=message.window,
                    route=message.route
                )
                await self.message_handler(message=message)

    async def ws_handler_asgi(self, receive: Callable, send: Callable, cookies: dict[str, str] | None = None):
        ws_connection: str = None
        handshake_cookies = cookies or {}

        try:
            while True:
                raw_message = await receive()

                if raw_message.get('type') == 'websocket.connect':
                    await send({'type': 'websocket.accept'})
                elif raw_message.get('type') == 'websocket.receive':
                    text = raw_message.get('text', raw_message.get('bytes', None))

                    if text:
                        raw_message = self.process_ws_message_handler(message=text)

                        if raw_message:
                            message = wsMessage(raw_message=raw_message, app=self.app, ws=self)

                            if message.window_response:
                                await self.set_window_response(message.window_response, message.session_id)

                            if message.file_content:
                                await self.set_file_content(message.file_content, message.session_id)

                            session_id, sync_template, _is_new = await self._ensure_session_and_template(
                                message,
                                connection_id=ws_connection,
                                cookies=handshake_cookies,
                                send_target=send,
                            )
                            ws_connection = session_id

                            if message.type and message.event_ref and not event_is_running(
                                message=message, task_manager=self.task_manager
                            ):
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
        headers = {
            (k.decode() if isinstance(k, bytes) else k).lower():
            (v.decode() if isinstance(v, bytes) else v)
            for k, v in scope.get('headers', [])
        }
        cookie_header = headers.get('cookie', '')
        cookies = {
            part.split('=', 1)[0].strip(): part.split('=', 1)[-1].strip()
            for part in cookie_header.split(';') if part.strip() and '=' in part
        }
        await self.ws_handler_asgi(receive=receive, send=send, cookies=cookies)

        for id, handler in self.ws_connections.items():
            if handler == send:
                sessions.remove_session(session_id=id)
                del self.ws_connections[id]
                break
