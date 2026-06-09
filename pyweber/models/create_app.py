from importlib import import_module, reload
from threading import Thread
from typing import Callable
from types import ModuleType
import os
import sys
from pathlib import Path

from pyweber.pyweber.pyweber import Pyweber
from pyweber.connection.http import HttpServer
from pyweber.connection.reload import ReloadServer
from pyweber.connection.websocket import WebsocketManager
from pyweber.utils.utils import PrintLine
from pyweber.config.config import config

DEFAULT_RELOAD_SKIP = (
    'alembic',
    'migrations',
    'sqlalchemy',
    'database',
    'db.engine',
    'db.session',
)


class CreatApp:
    def __init__(self, target: Callable, **kwargs):
        self.target = target
        self.app: Pyweber = None
        self.started = False
        self.__reload_mode = kwargs.get('reload_mode', None) or os.environ.get('PYWEBER_RELOAD_MODE') or config.get('session', 'reload_mode')
        self.__cert_file = kwargs.get('cert_file', None) or os.environ.get('PYWEBER_CERT_FILE') or config.get('server', 'cert_file')
        self.__key_file = kwargs.get('key_file', None) or os.environ.get('PYWEBER_KEY_FILE') or config.get('server', 'key_file')
        self.__server_host = kwargs.get('host', None) or os.environ.get('PYWEBER_SERVER_HOST') or config.get('server', 'host')
        self.__server_port = kwargs.get('port', None) or os.environ.get('PYWEBER_SERVER_PORT') or config.get('server', 'port')
        self.__server_route = kwargs.get('route', None) or os.environ.get('PYWEBER_SERVER_ROUTE') or config.get('server', 'route')
        self.mobile_mode = kwargs.get('mobile', None) or os.environ.get('PYWEBER_MOBILE_MODE') or config.get('server', 'mobile')
        self.__reload_skip_modules = tuple(
            kwargs.get('reload_skip_modules')
            or os.environ.get('PYWEBER_RELOAD_SKIP', '').split(',')
            or DEFAULT_RELOAD_SKIP
        )
        self.http_server = HttpServer()
        self.ws_server = WebsocketManager(app=self.app, protocol='pyweber')
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
        if self.__reload_mode in [True, 'True', 'true', 1, '1']:
            Thread(target=self.reload_server.start, daemon=True).start()
        
        self.http_server.run(
            route=self.__server_route,
            port=int(self.__server_port),
            host=self.__server_host,
            cert_file=self.__cert_file,
            key_file=self.__key_file,
            mobile=self.mobile_mode in [True, 'True', 'true', 1, '1']
        )
    
    @property
    def main_module(cls):
        return os.path.basename(os.path.abspath(sys.argv[0])).split('.')[0]
    
    def get_main_module(self):
        if self.main_module not in sys.modules:
            return import_module(self.main_module)
        if self.is_reloadable_module(self.main_module):
            return reload(sys.modules.get(self.main_module))
        return sys.modules.get(self.main_module)
    
    def project_modules(self):
        modules: dict[str, ModuleType] = {}

        for key, value in sys.modules.items():
            if hasattr(value, '__file__') and value.__file__ and str(self.project_path) in str(value.__file__):
                modules[key] = value
        return modules

    def _ordered_project_modules(self):
        return sorted(
            self.project_modules().items(),
            key=lambda item: item[0].count('.'),
            reverse=True,
        )

    def _should_reload_module(self, module_name: str, module: ModuleType) -> bool:
        if not self.is_reloadable_module(module_name):
            return False

        if module_name == '__main__':
            main_file = getattr(module, '__file__', None)
            if not main_file:
                return False
            return Path(main_file).resolve() == Path(sys.argv[0]).resolve()

        return True
    
    def path_to_module(self, filepath: str):
        rel_path = Path(filepath).resolve().relative_to(self.project_path)
        module_path = rel_path.with_suffix('')

        return '.'.join(module_path.parts)

    def is_reloadable_module(self, module_name: str) -> bool:
        lower = module_name.lower().replace('\\', '.').replace('/', '.')
        return not any(skip.strip() and skip.strip().lower() in lower for skip in self.__reload_skip_modules)

    def reset_reload_globals(self):
        from pyweber.connection.session import sessions

        for session_id in list(sessions.all_sessions):
            sessions.remove_session(session_id)

    def reload_modules(self, changed_file: str):
        try:
            if changed_file and str(changed_file).endswith('.py'):
                try:
                    module_name = self.path_to_module(filepath=changed_file)
                except ValueError:
                    module_name = None

                if module_name and module_name not in sys.modules:
                    import_module(module_name)

                for key, module in self._ordered_project_modules():
                    if not self._should_reload_module(key, module):
                        continue
                    try:
                        reload(module)
                    except Exception as exc:
                        PrintLine(
                            text=f'Error reloading module {key}: {exc}',
                            level='WARNING',
                        )

                self.reset_reload_globals()

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
            self.app.clear_cache_templates()

        self.app = self.get_app_instances()
        self.ws_server.app = self.app
        self.app.ws_server = self.ws_server

        if self.target:
            getattr(self.module, self.target.__name__)(self.app)
        
        self.http_server.app = self.app
        self.http_server.task_manager = self.app.ws_server.task_manager
        self.app.ws_server.app = self.app

    def update(self, module: str = None):
        self.started = True
        self.reload_modules(changed_file=module)