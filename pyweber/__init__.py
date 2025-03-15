import sys, os, importlib
from threading import Thread
from .utils.types import Events, EventType, JWTAlgorithms
from .utils.defaults import SERVER, SESSION, CONFIGFILE
from .utils.exceptions import *
from .utils.events import EventHandler
from .core.elements import Element
from .core.template import Template
from .server.server import Server
from .server.reload import ReloadServer
from .router.router import Router
from .utils.request import Request

"""A powerfull framework do create and manage a web page"""

__all__ = [
    'Template',
    'Element',
    'EventType'
    'Events',
    'JWTAlgorithms'
    'EventHandler',
    'Router',
    'Request'
    'run'
]

__version__ = '0.5.2'

class run:
    def __init__(self, target: callable = None):
        self.__target_function = target
        self.__target_module = os.path.splitext(os.path.basename(sys.argv[0]))[0]
        self.__module = self.__import_current_module()

        self.__configs = self.__read_config_file
        self.__route = self.__configs['server'].get('route', SERVER.ROUTE.value)
        self.__port = self.__configs['server'].get('port', SERVER.PORT.value)
        self.__host = self.__configs['server'].get('host', SERVER.HOST.value)

        self.__server: Server = None
        self.__router: Router = self.__get_router_instances(self.__module) or Router(update_handler=self.update)
        self.__reload_server = ReloadServer(event=self.update, reload=self.__configs['session'].get('reload_mode', SESSION.RELOAD_MODE.value))
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

        if self.__target_function:
            self.__router.clear_routes
            self.__router.clear_middleware
            self.__module = self.__import_current_module()
            self.target = getattr(self.__module, self.__target_function.__name__)
            self.target(self.__router)
        
        elif self.__get_router_instances(self.__import_current_module()):
            self.__module = self.__import_current_module()
            self.__router = self.__get_router_instances(module=self.__module)
        
        else:
            raise ValueError('None Router instance was created. Consider to create ou user main function instead')

        self.__reload_server.router = self.__router
        self.__server = Server(self.__router)
    
    def update(self):
        print('♻  Actualizando as rotas no servidor...')
        self.__load_target()
        self.__server.router = self.__router
    
    @property
    def __read_config_file(self):
        try:
            return CONFIGFILE.read_file()
        
        except FileNotFoundError:
            return {'server': {}, 'session': {}}
    
    def __import_current_module(self):
        module = importlib.import_module(self.__target_module)
        importlib.reload(module=module)
        return module
    
    def __get_router_instances(self, module):
        for name, obj in vars(module).items():
            if isinstance(obj, Router):
                obj._Router__update_handler = self.update
                return obj
        
        return None