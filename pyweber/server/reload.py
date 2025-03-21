import asyncio
import hashlib
import os
from time import time
from threading import Thread
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from pyweber.server.websocket import websockets
from pyweber.utils.utils import Colors, print_line

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
        self.start_server_time = time()
        self.ignore_reload_time = 10
        self.hash_files: dict[str, str] = {}
        self.file_extensions: list[str] = ['.css', '.html', '.js', '.py']
    
    def get_hash_file(self, file_path):
        try:
            with open(file_path, 'rb') as file:
                return hashlib.sha256(file.read()).hexdigest()
        except Exception:
            return None

    def on_modified(self, event):
        if time() - self.start_server_time < self.ignore_reload_time:
            return
        
        if any(event.src_path.endswith(ext) for ext in self.file_extensions):
            new_hash = self.get_hash_file(file_path=event.src_path)
            old_hash = self.hash_files.get(event.src_path, None)
            green = Colors.GREEN.value
            reset = Colors.RESET.value

            if new_hash and new_hash != old_hash:
                print_line(text=f'♻  File {green}{os.path.basename(event.src_path)}{reset} modified. Reloading...')
                print_line(text=f'♻  Restarting the server...')
                self.reload_server.event()
                print_line(text=f'♻  Server restarted...')
                print_line(text=f'♻  Reloading client...')
                asyncio.run_coroutine_threadsafe(
                    self.reload_server.websockets.send_reload(),
                    self.reload_server.websockets.loop
                )
                self.hash_files[event.src_path] = new_hash