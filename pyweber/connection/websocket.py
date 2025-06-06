import json
import inspect
import asyncio
import ssl
from uuid import uuid4
import websockets as ws
from threading import Thread, Lock
from typing import Callable, TYPE_CHECKING, Awaitable
from concurrent.futures import ThreadPoolExecutor, Future
from websockets.asyncio.server import serve as async_serve
from pyweber.models.ws_message import wsMessage
from pyweber.utils.utils import PrintLine, Colors
from pyweber.connection.session import sessions, Session
from pyweber.models.template_diff import TemplateDiff

if TYPE_CHECKING:
    from pyweber.pyweber.pyweber import Pyweber
    from pyweber.core.template import Template

class WsServer:
    def __init__(self, host: str, port: int, cert_file: str, key_file: str):
        self.host: str = host
        self.port: int = port
        self.app: 'Pyweber' = None
        self.ws_connections: set[ws.server.ServerConnection] = set()
        self.color_red = Colors.RED
        self.color_reset = Colors.RESET
        self.cert_file = cert_file
        self.key_file = key_file
        self.ssl_context = None
        self.task_manager = TaskManager()
        self.window_response: dict[str, (int, str)] = {}
        self.old_template: 'Template' = None
    
    async def ws_handler(self, websocket: ws.server.ServerConnection):
        try:
            async for message in websocket:
                raw_message = json.loads(message)

                message = wsMessage(raw_message=raw_message, app=self.app, ws=self)
                self.window_response = message.window_response
                sync_template = await message.template
                self.old_template = sync_template.clone

                if not message.session_id or message.session_id not in sessions.all_sessions:
                    websocket.id = message.session_id or str(websocket.id)
                    sessions.add_session(
                        session_id=websocket.id,
                        Session=Session(
                            template= sync_template,
                            window=message.window,
                            session_id=websocket.id
                        )
                    )
                    self.ws_connections.add(websocket)
                    await websocket.send(json.dumps({'setSessionId': websocket.id}))
                
                if message.type and message.event_ref and not event_is_running(message=message, task_manager=self.task_manager):
                    sessions.get_session(session_id=message.session_id).template = sync_template
                    sessions.get_session(session_id=message.session_id).window = message.window
                    await self.ws_message(message=message)
        
        except Exception as e:
            PrintLine(f'Error [ws]: {self.color_red}{e}{self.color_reset}')
            raise

        finally:
            await self.task_manager.cancel_session_handlers(session_id=websocket.id)
            await self.task_manager.cancel_all_tasks_async(session_id=websocket.id)
            self.ws_connections.discard(websocket)
            sessions.remove_session(session_id=websocket.id)
    
    async def ws_message(self, message: wsMessage):
        from pyweber.core.events import EventConstrutor
        event_handler = EventConstrutor(
            target_id=message.target_uuid,
            app=self.app,
            ws=self,
            session=sessions.get_session(session_id=message.session_id),
            route=message.route,
            event_data=message.event_data,
            event_type=message.type
        ).build_event

        if event_handler.element:
            event_id = event_handler.element.events.__dict__.get(f'on{message.type}')
            template_events = sessions.get_session(session_id=message.session_id).template.events
            
            if event_id and event_id in template_events:
                handler = template_events.get(event_id)

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
        
        self.send_message(
            data={
                'template': self.get_template_diff(
                    old_template=self.old_template,
                    new_template=sessions.get_session(session_id=message.session_id).template
                ),
                'window': sessions.get_session(session_id=message.session_id).window.get_all_event_ids
            },
            session_id=message.session_id
        )
    
    def get_template_diff(self, old_template: 'Template', new_template: 'Template'):
        return get_template_diff(old_template=old_template, new_template=new_template)
    
    def send_message(self, data: dict[str, (str, int)], session_id: str):
        ws_conn = next((ws for ws in self.ws_connections if ws.id == session_id), None)

        try:
            if ws_conn:
                try:
                    asyncio.create_task(ws_conn.send(json.dumps(data, ensure_ascii=False, indent=4)))
                except:
                    ws_conn.send(json.dumps(data, ensure_ascii=False, indent=4))
            else:
                for ws_conn in self.ws_connections:
                    try:
                        asyncio.create_task(ws_conn.send(json.dumps(data, ensure_ascii=False, indent=4)))
                    except:
                        ws_conn.send(json.dumps(data, ensure_ascii=False, indent=4))
                    
                    PrintLine(text=f'Enviei o reload para {ws_conn.id}')
        
        except Exception as e:
            PrintLine(text=f'{self.color_red}Error to send message: {e}{self.color_reset}')
            raise
    
    async def async_send_message(self, data: dict[str, (str, int)], session_id: str):
        ws_conn = next((ws for ws in self.ws_connections if ws.id == session_id), None)

        try:
            if ws_conn:
                await ws_conn.send(json.dumps(data, ensure_ascii=False, indent=4))

            else:
                for ws_conn in self.ws_connections:
                    await ws_conn.send(json.dumps(data, ensure_ascii=False, indent=4))
        
        except Exception as e:
            PrintLine(text=f'{self.color_red}Error to send message: {e}{self.color_reset}')
            raise
    
    async def get_window_response(self, timeout: int):
        import time
        start_time = time.time()

        while time.time() - start_time < timeout:
            await asyncio.sleep(0.1)

            if self.window_response:
                return self.window_response
        
        return {}
    
    def ssl_setup(self):
        try:
            self.ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            self.ssl_context.load_cert_chain(certfile=self.cert_file, keyfile=self.key_file)
        except Exception as e:
            PrintLine(f'{Colors.RED}WebSocket SSL configuration failed: {e}{Colors.RESET}')
            self.ssl_context = None

    async def ws_start(self):
        try:
            if self.cert_file and self.key_file:
                self.ssl_setup()

            if self.ssl_context:
                PrintLine(text=f"Server [ws] is running in wss://{self.host}:{self.port}")
            else:
                PrintLine(text=f"Server [ws] is running in ws://{self.host}:{self.port}")
            
            async with async_serve(self.ws_handler, self.host, self.port, ssl=self.ssl_context) as server:
                await server.serve_forever()
                
        except OSError as e:
            PrintLine(f"{Colors.RED}WebSocket server error: {e}{Colors.RESET}")
        except Exception as e:
            PrintLine(f"{Colors.RED}Unexpected error in WebSocket server: {e}{Colors.RESET}")

class WsServerAsgi:
    def __init__(self, app: 'Pyweber'):
        self.app = app
        self.ws_connections: set[str] = set()
        self.task_manager = TaskManager()
        self.window_response: dict[str, (int, str)] = {}
        self.old_template: 'Template' = None
        self.send_connectins: dict[str, Callable] = {}
    
    async def ws_handler(self, scope, receive, send):
        ws_id = None
        try:
            while True:
                raw_message = await receive()
                
                if raw_message.get('type') == 'websocket.connect':
                    await send({'type': 'websocket.accept'})

                elif raw_message.get('type') == 'websocket.receive':
                    text: str = raw_message.get('text', None)

                    if text:
                        raw_message = json.loads(text)
                        message = wsMessage(raw_message=raw_message, app=self.app, ws=self)
                        self.window_response = message.window_response
                        sync_template = await message.template
                        self.old_template = sync_template.clone

                        if not message.session_id or message.session_id not in sessions.all_sessions:
                            ws_id = message.session_id or str(uuid4())
                            sessions.add_session(
                                session_id=ws_id,
                                Session=Session(
                                    template=sync_template,
                                    window=message.window,
                                    session_id=ws_id
                                )
                            )

                            self.send_connectins[message.session_id] = send

                            self.send_message(
                                data={'setSessionId': ws_id},
                                session_id=message.session_id
                            )
                        
                        if message.type and message.event_ref and not event_is_running(message=message, task_manager=self.task_manager):
                            ws_id = message.session_id
                            self.send_connectins[message.session_id] = send
                            sessions.get_session(session_id=message.session_id).template = sync_template
                            sessions.get_session(session_id=message.session_id).window = message.window
                            await self.ws_message(message=message)

                else:
                    break
                
        except Exception as e:
            print(f'Error [ws asgi]: {e}')
            raise
        
        finally:
            await self.task_manager.cancel_session_handlers(session_id=ws_id)
            await self.task_manager.cancel_all_tasks_async(session_id=ws_id)
            self.ws_connections.discard(ws_id)
            sessions.remove_session(session_id=ws_id)
    
    async def ws_message(self, message: wsMessage):
        from pyweber.core.events import EventConstrutor
        event_handler = EventConstrutor(
            target_id=message.target_uuid,
            app=self.app,
            ws=self,
            session=sessions.get_session(session_id=message.session_id),
            route=message.route,
            event_data=message.event_data,
            event_type=message.type
        ).build_event

        if event_handler.element:
            event_id = event_handler.element.events.__dict__.get(f'on{message.type}')
            template_events = sessions.get_session(session_id=message.session_id).template.events
            
            if event_id and event_id in template_events:
                handler = template_events.get(event_id)

                if inspect.iscoroutinefunction(handler):
                    if message.session_id in self.task_manager.active_handlers_async:
                        if event_id not in self.task_manager.active_handlers_async[message.session_id]:
                            await self.task_manager.create_task_async(
                                session_id=message.session_id,
                                event_id=event_id,
                                handler=handler,
                                event_handler=event_handler
                            )
                    else:
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
        
        self.send_message(
            data= {
                'template': self.get_template_diff(
                    old_template=self.old_template,
                    new_template=sessions.get_session(message.session_id).template
                ),
                'window': sessions.get_session(message.session_id).window.get_all_event_ids
            },
            session_id=message.session_id
        )
    
    def get_template_diff(self, old_template: 'Template', new_template: 'Template'):
        return get_template_diff(old_template=old_template, new_template=new_template)
        
    def send_message(self, data: dict[str, (str, int)], session_id: str):
        try:
            send = self.send_connectins.get(session_id)

            asyncio.create_task(
                send({
                    'type': 'websocket.send',
                    'text': json.dumps(data, ensure_ascii=False, indent=4)
                })
            )

        except Exception as e:
            print(f'Error [ws asgi]: {e}')
            raise
    
    async def async_send_message(self, data: dict[str, (str, int)], session_id: str):
        try:
            send = self.send_connectins.get(session_id)

            await send({
                'type': 'websocket.send',
                'text': json.dumps(data, ensure_ascii=False, indent=4)
            })

        except Exception as e:
            print(f'Error [ws asgi]: {e}')
            raise
    
    async def get_window_response(self, timeout: int):
        import time
        start_time = time.time()

        while time.time() - start_time < timeout:
            await asyncio.sleep(0.1)

            if self.window_response:
                return self.window_response
        
        return {}
    
    async def __call__(self, scope, receive, send):
        assert scope.get('type', None) == 'websocket'
        await self.ws_handler(scope, receive, send)

class TaskManager:
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=10)
        self.lock = Lock()
        self.active_handlers: dict[str, dict[str, Future]] = {}
        self.active_handlers_async: dict[str, dict[str, Future]] = {}
    
    async def create_task_async(self, session_id: str, event_id: str, handler: Awaitable, event_handler):
        
        if session_id not in self.active_handlers_async:
            self.active_handlers_async[session_id] = {}

        if event_id in self.active_handlers_async[session_id]:
            existing_task = self.active_handlers_async[session_id][event_id]
            if existing_task.done():
                del self.active_handlers_async[session_id][event_id]
            else:
                # Tarefa já em execução, não criar uma nova
                return event_id
        
        task = asyncio.create_task(self.__run_task_async(session_id, event_id, handler, event_handler))
        self.active_handlers_async[session_id][event_id] = task
        
        return event_id

    async def __run_task_async(self, session_id: str, event_id: str, handler, event_handler):
        try:
            return await handler(event_handler)
        except asyncio.CancelledError:
            # Tarefa foi cancelada normalmente
            raise
        except Exception as e:
            # Capturar qualquer outra exceção
            PrintLine(f"Error on async handler ({event_id}): {e}")
            raise e

        finally:
            if session_id in self.active_handlers_async and event_id in self.active_handlers_async[session_id]:
                del self.active_handlers_async[session_id][event_id]

                if not self.active_handlers_async[session_id]:
                    del self.active_handlers_async[session_id]
    
    async def cancel_all_tasks_async(self, session_id: str) -> int:
        count = 0
        if session_id in self.active_handlers_async:
            tasks = list(self.active_handlers_async[session_id].items())
            
            for event_id, task in tasks:
                if not task.done():
                    task.cancel()
                    count += 1
            
            del self.active_handlers_async[session_id]
        
        return count

    
    def create_task(self, session_id: str, event_id: str, handler: Callable, event_handler):
        session_handlers = self.active_handlers.get(session_id, {})

        if session_handlers and session_handlers.get(event_handler, None):
            return False
        
        future = self.executor.submit(
            self.__run_executor,
            session_id,
            event_id,
            handler,
            event_handler
        )

        if session_id not in self.active_handlers:
            self.active_handlers[session_id] = {}
        
        self.active_handlers[session_id][event_id] = future

        return True
    
    def __run_executor(self, session_id: str, event_id: str, handler: Callable, event_handler):
        
        try:
            result = handler(event_handler)
            return result
        except Exception as e:
            PrintLine(text=f'Error on sync handler ({event_id}): {e}')
            raise e

        finally:
            if session_id in self.active_handlers:
                if event_id in self.active_handlers[session_id]:
                    del self.active_handlers[session_id][event_id]
            
            if not self.active_handlers[session_id]:
                del self.active_handlers[session_id]
    
    async def cancel_session_handlers(self, session_id: str):
        if session_id:
            if session_id in self.active_handlers:
                for event_id, future in self.active_handlers[session_id].items():
                    if future and not future.done():
                        future.cancel()
                
                del self.active_handlers[session_id]
        else:
            for session_id in self.active_handlers:
                for event_id, future in self.active_handlers[session_id].items():
                    if future and not future.done():
                        future.cancel()
                
                if not self.active_handlers[session_id]:
                    del self.active_handlers[session_id]
    
    def shutdown(self):
        self.executor.shutdown(wait=False, cancel_futures=True)

def event_is_running(message: wsMessage, task_manager: TaskManager) -> bool:
    """Check if event is running"""
    if message.session_id in task_manager.active_handlers_async:
        template = sessions.get_session(session_id=message.session_id).template
        event_id = template.getElementByUUID(message.target_uuid).events.__dict__.get(f'on{message.type}')

        if event_id in task_manager.active_handlers_async[message.session_id]:
            return True
    
    return False

def get_template_diff(old_template: 'Template', new_template: 'Template'):
    return TemplateDiff(new_element=new_template.root, old_element=old_template.root).differences