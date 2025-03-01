from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from threading import Thread
import websockets
import asyncio
from time import time

class ReloadServer:
    def __init__(self, port: int = 8765, event = None):
        self.websocket_clients: set[websockets.WebSocketClientProtocol] = set()
        self.port = port
        self.host = 'localhost'
        self.event = event
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
    
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
            await websocket.wait_closed()
        
        finally:
            self.websocket_clients.remove(websocket)
    
    async def ws_start(self):
        try:
            async with websockets.serve(self.ws_handler, self.host, self.port):
                await asyncio.Future()
        
        except:
            pass
    
    def run(self):
        Thread(target=self.loop.run_until_complete, args=(self.ws_start(),), daemon=True).start()

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