"""
PyWeber - A powerful framework to create and manage web applications

PyWeber provides abilities for creating dynamic web pages with Python,
including template management, routing, and real-time updates.
"""

# standards library imports
import sys
import os
import importlib
from threading import Thread

# core components
from .core.element import Element
from .core.template import Template

# router components
from .router.router import Router
from .router.request import Request

# server components
from .server.server import Server
from .server.reload import ReloadServer

# events components
from .utils.events import EventHandler
from .utils.types import Events, EventType, HTMLTag

# Utility, Helpers and Exceptions
from .utils.types import JWTAlgorithms
from .utils.utils import print_line
from .config.config import config
from .utils.exceptions import *

# version information
__version__ = '0.8.1'

__all__ = [
    'Template',
    'Element',
    'EventType',
    'Events',
    'HTMLTag',
    'JWTAlgorithms',
    'EventHandler',
    'Router',
    'Request',
    'run'
]

def run(target: callable = None):
    """
    Run a PyWeber application.

    Args:
        target: Function that sets up routes or module with Router instance

    Example:
    ```python
    import pyweber as pw

    class Home:
        def __init__(app: pw.Router):
            super().__init__(template='Hello world')
            self.app = app

    def main(app: pw.Router):
        app.add_route('/', template=Home(app=app))

    if __name__ == '__main__':
        pw.run(target=main)
    ```
    ---
    Get more: https://pyweber.readthedocs.io/en/latest
    """

    if target:
        if not callable(target):
            raise ValueError("The target that you specify is'nt callable function")
    
    SetupApplication(target=target).run()

class SetupApplication:
    def __init__(self, target: callable = None):
        self.__target_function = target
        self.__target_module = os.path.splitext(os.path.basename(sys.argv[0]))[0]
        self.__module = self.import_module()
        self.__router: Router = self.get_router_instances()
        self.reload_server = ReloadServer(
            host=config['websocket'].get('host'),
            port=config['websocket'].get('port'),
            event=self.update,
            reload=config['session'].get('reload_mode')
        )
        self.__server = Server()
    
    def run(self):
        self.load_target()
        Thread(target=self.reload_server.run, daemon=True).start()
        self.__server.run(
            route=config['server'].get('route'),
            port=config['server'].get('port'),
            host=config['server'].get('host')
        )
    
    def import_module(self):
        try:
            module = importlib.import_module(self.__target_module)
            importlib.reload(module=module)
            return module
        
        except ImportError as e:
            print(f'Error to import: {e}')
            return None
    
    def get_router_instances(self):
        if not self.__module:
            return None
        
        router = Router(update_handler=self.update)

        for _, obj in vars(self.__module).items():
            if isinstance(obj, Router):
                obj = router
                return obj
            
        return router
    
    def load_target(self):
        self.__router.clear_routes
        self.__router.clear_middleware
        self.__module = self.import_module()
        self.__router = self.get_router_instances()

        if self.__target_function:
            getattr(self.__module, self.__target_function.__name__)(self.__router)
        
        self.__server.router = self.__router
        self.reload_server.websockets.router = self.__router
    
    def update(self):
        print_line(text='♻  Restaring process again')
        self.load_target()