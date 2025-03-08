import sys, os, importlib, json
from threading import Thread
from pathlib import Path
from .utils.types import Events, EventType
from .utils.defaults import SERVER, SESSION, CONFIGFILE
from .utils.exceptions import *
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
    'EventType'
    'Events',
    'EventHandler',
    'Router',
    'run'
]

__version__ = '0.5.1'

class run:
    def __init__(self, target: callable):
        self.__configs = CONFIGFILE.config_file()
        self.__route = self.__configs['server'].get('route', SERVER.ROUTE.value)
        self.__port = self.__configs['server'].get('port', SERVER.PORT.value)
        self.__host = self.__configs['server'].get('host', SERVER.HOST.value)
        self.__target_function = target
        self.__target_module = os.path.splitext(os.path.basename(sys.argv[0]))[0]
        self.__router: Router = Router(update_handler=self.update)
        self.__server: Server = None
        self.__reload_server = ReloadServer(
            event=self.update,
            reload=self.__configs['session'].get('reload_mode', SESSION.RELOAD_MODE.value)
        )
        self.__run()

    def __run(self):
        self.__load_target()
        self.__reload_server.router = self.__router
        Thread(target=self.__reload_server.run, daemon=True).start()

        self.__server.run(
            route=self.__route,
            port=self.__port,
            host=self.__host,
            secret_key=self.__configs['session'].get('secret_key', SESSION.SECRET_KEY.value)
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