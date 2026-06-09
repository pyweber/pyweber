import os
import asyncio
import hashlib
from time import time
from watchdog.observers import Observer
from typing import Callable, Awaitable
from watchdog.events import FileSystemEventHandler

from pyweber.utils.utils import Colors, PrintLine

# Only these extensions restart Python modules / app routes.
_SERVER_RELOAD_EXTENSIONS = ('.py', '.toml')

# Directories ignored when seeding file hashes at startup.
_IGNORED_DIRS = frozenset({
    '__pycache__', '.git', '.pyweber', 'node_modules', '.venv', 'venv',
    'site', '.pytest_cache', '.mypy_cache', 'dist', 'build', '.eggs',
})


class ReloadServer:
    def __init__(
            self,
            ws_reload: Callable[..., Awaitable],
            http_reload: Callable,
            watch_path: str = '.',
            extension_files: list[str] = [],
            ignore_reload_time: float = 10,
            reload_cooldown: float = 1.0,
        ):
        assert callable(ws_reload) and callable(http_reload)
        self.ws_reload = ws_reload
        self.http_reload = http_reload
        self.watch_path = watch_path
        self.watch_file_extensions = extension_files
        self.ignore_reload_time = ignore_reload_time
        self.reload_cooldown = reload_cooldown

    def start(self):
        asyncio.run(WatchDogFiles(self).start())

class WatchDogFiles:
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

class ReloadHandler(FileSystemEventHandler):
    def __init__(self, reload_server: ReloadServer):
        self.reload_server = reload_server
        self.start_server_time = time()
        self.hash_files: dict[str, str] = {}
        self._last_reload_at = 0.0
        self._seed_hashes()

    @staticmethod
    def _normalize_path(file_path: str) -> str:
        return os.path.normcase(os.path.abspath(file_path))

    def _seed_hashes(self):
        """Record initial hashes so the first watchdog event is not treated as a change."""
        watch_path = os.path.abspath(self.reload_server.watch_path)
        extensions = self.reload_server.watch_file_extensions

        if not os.path.isdir(watch_path):
            return

        for root, dirs, files in os.walk(watch_path):
            dirs[:] = [d for d in dirs if d not in _IGNORED_DIRS]
            for name in files:
                if not any(name.endswith(ext) for ext in extensions):
                    continue
                path = self._normalize_path(os.path.join(root, name))
                digest = self.get_hash_file(path)
                if digest:
                    self.hash_files[path] = digest

    def get_hash_file(self, file_path):
        try:
            with open(file_path, 'rb') as file:
                return hashlib.sha256(file.read()).hexdigest()
        except Exception:
            return None

    def on_modified(self, event):
        if getattr(event, 'is_directory', False):
            return

        if time() - self.start_server_time < self.reload_server.ignore_reload_time:
            return

        path = self._normalize_path(event.src_path)

        if not any(path.endswith(ext) for ext in self.reload_server.watch_file_extensions):
            return

        new_hash = self.get_hash_file(file_path=path)
        if not new_hash:
            return

        old_hash = self.hash_files.get(path)

        # Unknown file: store baseline without reloading.
        if old_hash is None:
            self.hash_files[path] = new_hash
            return

        if new_hash == old_hash:
            return

        now = time()
        if now - self._last_reload_at < self.reload_server.reload_cooldown:
            self.hash_files[path] = new_hash
            return

        self._last_reload_at = now
        self.hash_files[path] = new_hash

        green = Colors.GREEN
        reset = Colors.RESET
        PrintLine(
            text=f'♻  File {green}{os.path.basename(path)}{reset} modified. Reloading...'
        )

        self.restart_server(path)
        PrintLine(text='♻  Reloading client...')
        asyncio.run(self.reload_server.ws_reload(data={'reload': True}, session_id=None))

    def restart_server(self, changed_file: str):
        if any(changed_file.endswith(ext) for ext in _SERVER_RELOAD_EXTENSIONS):
            if changed_file.endswith('.py'):
                PrintLine(text='♻  Restarting the server...')
            self.reload_server.http_reload(changed_file)
            if changed_file.endswith('.py'):
                PrintLine(text='♻  Server restarted...')
