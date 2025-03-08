import sys, os, importlib, json
from threading import Thread
from pathlib import Path
from .utils.types import Events
from .utils.events import EventHandler
from .core.elements import Element
from .core.template import Template
from .server.server import Server
from .server.reload import ReloadServer
from .router.router import Router

"""A powerfull framework do create and manage a web page"""

__all__ = [
    'Template',
    'Element',
    'Events',
    'EventHandler',
    'Router',
    'run'
]

__version__ = '0.4.0'

class run:
    def __init__(self, target, route: str = '/', port: int = 8800, host: str='localhost'):
        self.__route = route
        self.__port = port
        self.__host = host
        self.__target_function = target
        self.__target_module = os.path.splitext(os.path.basename(sys.argv[0]))[0]
        self.__router: Router = Router()
        self.__server: Server = None
        self.__reload_server = ReloadServer(event=self.update, reload=self.__reload_mode)
        self.__run()


    def __run(self):
        self.__load_target()
        self.__reload_server.router = self.__router
        Thread(target=self.__reload_server.run, daemon=True).start()

        self.__server.run(
            route=self.__route,
            port=self.__port,
            host=self.__host
        )
    
    def __load_target(self):
        self.__router.clear_routes
        module = importlib.import_module(self.__target_module)
        importlib.reload(module=module)
        self.target = getattr(module, self.__target_function.__name__)
        self.target(self.__router)
        self.__reload_server.router = self.__router
        self.__server = Server(self.__router)
    
    def update(self):
        print('♻  Actualizando as rotas no servidor...')
        self.__load_target()
        self.__server.router = self.__router
    
    @property
    def __reload_mode(self) -> bool:
        project_name = Path('.pyweber')
        if Path.exists(Path.joinpath(project_name, 'config.json')):
            with open(Path.joinpath(project_name, 'config.json'), 'r+') as f:
                d: dict[str, bool] = json.load(f)

                return d.get('reload_mode', False)
        else:
            return False