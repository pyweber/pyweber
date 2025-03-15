import asyncio
from time import time
from threading import Thread
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from pyweber.server.websocket import websockets

class ReloadServer:
    def __init__(self, host: str = 'localhost', port: int = 8765, event: callable = None, reload: bool = False):
        self.websockets = websockets(
            host=host,
            port=port
        )
        self.reload = reload
        self.event = event
    
    def run(self):
        Thread(
            target=self.websockets.loop.run_until_complete,
            args=(self.websockets.ws_start(),),
            daemon=True
        ).start()

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
                asyncio.run_coroutine_threadsafe(
                    self.reload_server.websockets.send_reload(),
                    self.reload_server.websockets.loop
                )
                self.last_time = time()