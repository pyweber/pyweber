import os
import asyncio
import hashlib
from time import time
from watchdog.observers import Observer
from typing import Callable, Awaitable
from watchdog.events import FileSystemEventHandler

from pyweber.utils.utils import Colors, PrintLine

class ReloadServer: # pragma: no cover
    def __init__(self, ws_reload: Callable[..., Awaitable], http_reload: Callable, watch_path: str = '.'):
        self.ws_reload = ws_reload
        self.http_reload = http_reload
        self.watch_path = watch_path
        self.watch_file_extensions: list[str] = ['.css', '.html', '.js', '.py']
        self.ignore_reload_time = 10
    
    def start(self):
        asyncio.run(WatchDogFiles(self).start())

class WatchDogFiles: # pragma: no cover
    def __init__(self, reload_server: ReloadServer):
        self.event_handler = ReloadHandler(reload_server)
        self.observer = Observer()
    
    async def start(self):
        self.observer.schedule(
            event_handler=self.event_handler,
            path=self.event_handler.reload_server.watch_path,
            recursive=True
        )
        self.observer.start()

        try:
            while True:
                await asyncio.sleep(1)
        
        except KeyboardInterrupt:
            self.observer.stop()
        
        self.observer.join()

class ReloadHandler(FileSystemEventHandler): # pragma: no cover
    def __init__(self, reload_server: ReloadServer):
        self.reload_server = reload_server
        self.start_server_time = time()
        self.hash_files: dict[str, str] = {}
    
    def get_hash_file(self, file_path):
        try:
            with open(file_path, 'rb') as file:
                return hashlib.sha256(file.read()).hexdigest()
        except Exception:
            return None
    
    def on_modified(self, event):
        if time() - self.start_server_time < self.reload_server.ignore_reload_time:
            return
        
        if any(event.src_path.endswith(ext) for ext in self.reload_server.watch_file_extensions):
            new_hash = self.get_hash_file(file_path=event.src_path)
            old_hash = self.hash_files.get(event.src_path, None)
            green = Colors.GREEN
            reset = Colors.RESET

            if new_hash and new_hash != old_hash:
                PrintLine(text=f'♻  File {green}{os.path.basename(event.src_path)}{reset} modified. Reloading...')
                PrintLine(text=f'♻  Restarting the server...')
                self.reload_server.http_reload()
                PrintLine(text=f'♻  Server restarted...')
                PrintLine(text=f'♻  Reloading client...')

                asyncio.run(self.reload_server.ws_reload(data={'reload': True}, session_id=None))
                self.hash_files[event.src_path] = new_hash