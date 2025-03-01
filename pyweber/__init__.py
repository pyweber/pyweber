from pyweber.templates.template import Template, Element
from pyweber.router.router import Router
from pyweber.server.server import Server
from pyweber.reload_server.reload_server import ReloadServer, Thread
import sys, os, importlib

"""A powerfull framework do create and manage a web page"""

__version__ = '0.3.0'

class run:
    def __init__(self, target, route: str = '/', reload: bool = True, port: int = 8800):
        self.__target_module = os.path.splitext(os.path.basename(sys.argv[0]))[0]
        self.__target_function = target
        self.route = route
        self.reload = reload
        self.port = port
        self.__router: Router = Router()
        self.__server: Server = None
        self.__run()


    def __run(self):
        self.load_target()

        if self.reload:
            reload_server = ReloadServer(event=self.update)
            Thread(target=reload_server.run, daemon=True).start()

        self.__server.run(
            route=self.route,
            port=self.port,
            reload=self.reload
        )
    
    def load_target(self):
        self.__router.clear_routes
        module = importlib.import_module(self.__target_module)
        importlib.reload(module=module)
        self.target = getattr(module, self.__target_function.__name__)
        self.target(self.__router)
        self.__server = Server(self.__router)
    
    def update(self):
        print('Actualizando as rotas no servidor')
        self.load_target()
        self.__server.router = self.__router