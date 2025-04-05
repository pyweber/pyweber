from importlib import import_module, reload
from threading import Thread
import os
import sys

from pyweber.pyweber.pyweber import Pyweber
from pyweber.connection.http import HttpServer
from pyweber.connection.websocket import WsServer
from pyweber.connection.reload import ReloadServer
from pyweber.config.config import config

class CreatApp:
    def __init__(self, target: callable):
        self.target = target
        self.module = self.import_module()
        self.app = self.get_app_instances()
        self.http_server = HttpServer(update_handler=self.update)
        self.ws_server = WsServer(host=config['server'].get('host'), port=config['websocket'].get('port'))
        self.reload_server = ReloadServer(ws_reload=self.ws_server.send_reload, http_reload=self.update)
    
    @property
    def target(self):
        return self.__target
    
    @target.setter
    def target(self, target: callable):
        if not target:
            self.__target = None
            return
        
        if not callable(target):
            raise TypeError('The target must be callable function')
            
        self.__target = target
    
    def run(self):
        self.load_target()
        Thread(target=self.ws_server.ws_start, daemon=True).start()

        if config['session'].get('reload_mode'):
            Thread(target=self.reload_server.start, daemon=True).start()
        
        self.http_server.run(
            route=config['server'].get('route'),
            port=config['server'].get('port'),
            host=config['server'].get('host')
        )
    
    def import_module(self):
        try:
            return reload(import_module(name=os.path.splitext(os.path.basename(sys.argv[0]))[0]))
        
        except Exception as e:
            raise ImportError(f'Error to import module: {e}')
    
    def get_app_instances(self):

        for _, obj in vars(self.module).items():
            if isinstance(obj, Pyweber):
                obj._Pyweber__update_handler = self.update
                return obj
        
        return Pyweber(update_handler=self.update)
    
    def load_target(self):
        self.app.clear_routes
        self.app.clear_after_request
        self.app.clear_before_request
        self.module = self.import_module()
        self.app = self.get_app_instances()

        if self.target:
            getattr(self.module, self.target.__name__)(self.app)
        
        self.http_server.app = self.app
        self.ws_server.app = self.app

    def update(self):
        self.load_target()