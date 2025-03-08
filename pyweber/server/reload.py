import json
import asyncio
import websockets
from time import time
from threading import Thread
from base64 import b64decode, b64encode
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from pyweber.router.router import Router
from pyweber.utils.events import EventConstrutor
from pyweber.core.template import Template
from pyweber.core.elements import Element
from pyweber.utils.exceptions import RouteNotFoundError

class ReloadServer:
    def __init__(self, port: int = 8765, event = None, reload: bool = False):
        self.websocket_clients: set[websockets.WebSocketClientProtocol] = set()
        self.port = port
        self.host = 'localhost'
        self.event = event
        self.reload = reload
        self.router: Router = None
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.event_hander = None
    
    async def send_reload(self):
        if self.websocket_clients:
            for client in self.websocket_clients:
                try:
                    if client.open:
                        await client.send('reload')

                except Exception as e:
                    print(f'Erro ao actualizar cliente: {e}')
    
    async def ws_handler(self, websocket: websockets.WebSocketClientProtocol, _):
        self.websocket_clients.add(websocket)

        try:
            async for message in websocket:
                await self.handle_message(message, websocket)
        
        finally:
            self.websocket_clients.remove(websocket)
    
    async def handle_message(self, message: str, websocket: websockets.WebSocketClientProtocol):
        """Processa uma mensagem recebida do navegador."""
        try:
            event_json = json.loads(message)
            last_template = self.update_template_root(event=event_json)
            event_handler = EventConstrutor(
                event=self.update_event(
                    event=event_json,
                    template=last_template
                )
            ).build_event

            if event_handler.element:
                event_id = event_handler.element.events.__dict__.get(f'on{event_handler.event_type}', None)
                
                if event_id:
                    if event_id in last_template.events:
                        try:
                            last_template.events.get(event_id)(event_handler)
                            new_html = b64encode(last_template.build_html().encode('utf-8')).decode('utf-8')
                            await websocket.send(json.dumps({'template': new_html}, ensure_ascii=False, indent=4))
                        
                        except Exception as e:
                            await websocket.send(json.dumps({'Error': str(e)}))
        
        except json.JSONDecodeError:
            print(f"Mensagem inválida recebida: {message}")
    
    def update_template_root(self, event: dict[str, None]) -> Template:
        try:
            last_template = self.router.get_route(route=event['route'])
            html = b64decode(event['template']).decode('utf-8')
            values: dict[str, None] = json.loads(b64decode(event['values']).decode('utf-8'))
            new_root_element = last_template.parse_html(html=html)
            self.insert_values(root_Element=new_root_element, values=values)
            last_template.root = new_root_element
            
        except RouteNotFoundError:
            last_template = self.router.page_not_found
        
        return last_template
    
    def update_event(self, event: dict[str, None], template: Template):
        event['template'] = template
        return event
    
    def insert_values(self, root_Element: Element, values: dict[str, None]):
        root_Element.value = values.get(root_Element.uuid, None)
        for child in root_Element.childs:
            self.insert_values(child, values)
    
    async def ws_start(self):
        try:
            async with websockets.serve(self.ws_handler, self.host, self.port):
                await asyncio.Future()
        
        except:
            pass
    
    def run(self):
        Thread(target=self.loop.run_until_complete, args=(self.ws_start(),), daemon=True).start()

        if self.reload:
            watchdog = WatchDogFiles(self)
            asyncio.run(watchdog.start())

class WatchDogFiles:
    def __init__(self, reload_server: ReloadServer):
        self.event_handler = ReloadHandler(reload_server)
        self.observer = Observer()
    
    async def start(self):
        self.observer.schedule(self.event_handler, path='.', recursive=True)
        self.observer.start()

        try:
            while True:
                await asyncio.sleep(1)
        
        except KeyboardInterrupt:
            self.observer.stop()
        
        self.observer.join()
        
class ReloadHandler(FileSystemEventHandler):
    def __init__(self, reload_server: ReloadServer):
        self.reload_server = reload_server
        self.last_time = 0
        self.file_extensions: list[str] = ['.css', '.html', '.js', '.py']

    def on_modified(self, event):
        if any(event.src_path.endswith(ext) for ext in self.file_extensions):

            if time() - self.last_time > 1:
                self.reload_server.event()
                print('♻  Actualizando templates...')
                asyncio.run_coroutine_threadsafe(self.reload_server.send_reload(), self.reload_server.loop)
                self.last_time = time()