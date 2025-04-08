from importlib import import_module, reload
from threading import Thread
from typing import Callable
import os
import sys

from pyweber.pyweber.pyweber import Pyweber
from pyweber.connection.http import HttpServer
from pyweber.connection.websocket import WsServer
from pyweber.connection.reload import ReloadServer
from pyweber.config.config import config

class CreatApp:
    def __init__(self, target: Callable, **kwargs):
        self.target = target
        self.module = self.import_module()
        self.app = self.get_app_instances()
        self.__reload_mode = os.environ.get('PYWEBER_RELOAD_MODE') or kwargs.get('reload_mode', None) or config.get('session', 'reload_mode')
        self.__cert_file = os.environ.get('PYWEBER_CERT_FILE') or kwargs.get('cert_file', None) or config.get('server', 'cert_file')
        self.__key_file = os.environ.get('PYWEBER_KEY_FILE') or kwargs.get('key_file', None) or config.get('server', 'key_file')
        self.__use_ssl = kwargs.get('https_enabled', None) or config.get('server', 'https_enabled')
        self.__server_host = os.environ.get('PYWEBER_SERVER_HOST') or kwargs.get('host', None) or config.get('server', 'host')
        self.__server_port = os.environ.get('PYWEBER_SERVER_PORT') or kwargs.get('port', None) or config.get('server', 'port')
        self.__server_ws_port = os.environ.get('PYWEBER_WS_PORT') or kwargs.get('ws_port', None) or config.get('websocket', 'port')
        self.__server_route = os.environ.get('PYWEBER_SERVER_ROUTE') or kwargs.get('route', None) or config.get('server', 'route')
        self.http_server = HttpServer(update_handler=self.update)
        self.ws_server = WsServer(
            host=self.__server_host,
            port=int(self.__server_ws_port),
            use_ssl=self.__use_ssl,
            cert_file=self.__cert_file,
            key_file=self.__key_file
        )
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
    
    def environ_vars(self, variable: str, /, default = None):
        return os.environ.get(variable, default=default)
    
    def run(self):
        self.load_target()
        Thread(target=self.ws_server.ws_start, daemon=True).start()

        if self.__reload_mode in [True, 'True', 1, '1']:
            Thread(target=self.reload_server.start, daemon=True).start()
        
        self.http_server.run(
            route=self.__server_route,
            port=int(self.__server_port),
            host=self.__server_host,
            use_https=self.__use_ssl,
            cert_file=self.__cert_file,
            key_file=self.__key_file
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