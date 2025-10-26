from importlib import import_module, reload
from threading import Thread
from typing import Callable
from types import ModuleType
import asyncio
import os
import sys
from pathlib import Path

from pyweber.pyweber.pyweber import Pyweber
from pyweber.connection.http import HttpServer
from pyweber.connection.websocket import WebSocket
from pyweber.connection.reload import ReloadServer
from pyweber.utils.utils import PrintLine
from pyweber.config.config import config

class CreatApp: # pragma: no cover
    def __init__(self, target: Callable, **kwargs):
        self.target = target
        self.app = None
        self.started = False
        self.__reload_mode = kwargs.get('reload_mode', None) or os.environ.get('PYWEBER_RELOAD_MODE') or config.get('session', 'reload_mode')
        self.__cert_file = kwargs.get('cert_file', None) or os.environ.get('PYWEBER_CERT_FILE') or config.get('server', 'cert_file')
        self.__key_file = kwargs.get('key_file', None) or os.environ.get('PYWEBER_KEY_FILE') or config.get('server', 'key_file')
        self.__server_host = kwargs.get('host', None) or os.environ.get('PYWEBER_SERVER_HOST') or config.get('server', 'host')
        self.__server_port = kwargs.get('port', None) or os.environ.get('PYWEBER_SERVER_PORT') or config.get('server', 'port')
        self.__server_ws_port = kwargs.get('ws_port', None) or os.environ.get('PYWEBER_WS_PORT') or config.get('websocket', 'port')
        self.__server_route = kwargs.get('route', None) or os.environ.get('PYWEBER_SERVER_ROUTE') or config.get('server', 'route')
        self.__disable_ws = kwargs.get('disable_ws', None) or os.environ.get('PYWEBER_DISABLE_WS') or config.get('websocket', 'disable_ws')
        self.http_server = HttpServer(update_handler=self.update)
        self.ws_server = WebSocket(app=self.app, protocol='pyweber')
        self.reload_server = ReloadServer(
            ws_reload=self.ws_server.send_message,
            http_reload=self.update,
            ignore_reload_time=kwargs.get('ignore_reload_time', None) or 10,
            extension_files=kwargs.get('reload_extensions', []) or ['.css', '.html', '.json', '.toml', '.js', '.py']
        )
    
    @property
    def target(self): return self.__target
    
    @target.setter
    def target(self, target: Callable):
        if not target:
            self.__target = None
            return
        
        if not callable(target):
            raise TypeError('The target must be callable function')
            
        self.__target = target
    
    @property
    def project_path(self): return Path(os.path.abspath(sys.argv[0])).parent
    
    def environ_vars(self, variable: str, /, default = None):
        return os.environ.get(variable, default=default)
    
    def run(self):
        self.load_target()
        if self.__disable_ws not in ['True', True, '1', 1]:
            Thread(target=asyncio.run, args=(self.ws_server.ws_start(
                    host=self.__server_host,
                    port=self.__server_ws_port,
                    cert_file=self.__cert_file,
                    key_file=self.__key_file
                ),), daemon=True
            ).start()

        if self.__reload_mode in [True, 'True', 1, '1']:
            Thread(target=self.reload_server.start, daemon=True).start()
        
        self.http_server.run(
            route=self.__server_route,
            port=int(self.__server_port),
            host=self.__server_host,
            cert_file=self.__cert_file,
            key_file=self.__key_file
        )
    
    def get_main_module(self):
        main_module = os.path.basename(os.path.abspath(sys.argv[0])).split('.')[0]

        if main_module in sys.modules:
            if not self.started:
                return sys.modules[main_module]
            return reload(sys.modules[main_module])
        
        return import_module(main_module)
    
    def project_modules(self):
        modules: dict[str, ModuleType] = {}

        for key, value in sys.modules.items():
            if hasattr(value, '__file__') and str(self.project_path) in str(value.__file__):
                modules[key] = value
        
        return modules
    
    def path_to_module(self, filepath: str):
        rel_path = Path(filepath).resolve().relative_to(self.project_path)
        module_path = rel_path.with_suffix('')

        return '.'.join(module_path.parts)

    def reload_modules(self, changed_file: str):
        try:
            if changed_file and str(changed_file).endswith('.py'):
                module_name = self.path_to_module(filepath=changed_file)

                if module_name in sys.modules:
                    for key, module in self.project_modules().items():
                        if key != '__main__' and getattr(module, '__spec__', None) is not None:
                            reload(module)
                else:
                    import_module(module_name)
            
            self.load_target()
        
        except Exception as e:
            PrintLine(text=f'Error to import module: {e}', level='ERROR')
            raise e
    
    def get_app_instances(self):
        self.module = self.get_main_module()

        for _, obj in vars(self.module).items():
            if isinstance(obj, Pyweber):
                obj._Pyweber__update_handler = self.update
                return obj

        return Pyweber(update_handler=self.update)
    
    def load_target(self):
        if self.started:
            self.app.clear_routes()
            self.app.clear_before_request_middleware()
            self.app.clear_after_request_middleware()

        self.app = self.get_app_instances()

        if self.target:
            getattr(self.module, self.target.__name__)(self.app)
        
        self.http_server.app = self.app
        self.http_server.task_manager = self.ws_server.task_manager
        self.ws_server.app = self.app

    def update(self, module: str = None):
        self.started = True
        self.reload_modules(changed_file=module)