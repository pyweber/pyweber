import socket
import select
import os
import shutil
import asyncio
from threading import Thread
from pyweber.pyweber.pyweber import Pyweber
from pyweber.models.request import Request
from pyweber.utils.utils import PrintLine, Colors

class HttpServer:
    def __init__(self, update_handler: callable):
        self.connections: list[socket.socket] = []
        self.route, self.port, self.host = None, None, None
        self.current_directory = os.path.abspath(__file__)
        self.update_server = update_handler
        self.started = False
    
    @property
    def app(self):
        return self.__app
    
    @app.setter
    def app(self, value: Pyweber):
        self.__app = value
    
    def is_file_request(self, request: Request):
        return '.' in request.path.split('/')[-1]

    async def handle_response(self, client: socket.socket):
        try:
            request = client.recv(1024).decode()

            if request:
                request=Request(raw_request=request)

                if self.started:
                    if not self.is_file_request(request):
                        self.update_server()
                
                response = await self.app.get_route(request=request)
                client.sendall(response.build_response)

                if not self.is_file_request(request):
                    self.started = True
        
        except BlockingIOError:
            pass
        
        finally:
            if client in self.connections:
                self.connections.remove(client)

            client.close()
    
    def create_server(self, restart: bool = False):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_server:
            client_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            try:
                client_server.bind((self.host, self.port))
                client_server.listen(5)

            except OSError as e:
                PrintLine(text=f'Error to running server: ')
                return
            
            except:
                PrintLine(text=f'Error [server] 1: {e}')
            
            if not restart:
                url = f'http://{self.host if self.host != '0.0.0.0' else '127.0.0.1'}:{self.port}{self.route}'
                PrintLine(text=f'Server online in {Colors.GREEN}{url}{Colors.RESET}')

            while True:
                try:
                    rlist, _, _ = select.select([client_server], [], [], 1)

                    if not rlist:
                        continue

                    else:
                        for server in rlist:
                            if server is client_server:
                                client_socket, _ = client_server.accept()
                                self.connections.append(server)

                                Thread(
                                    target=asyncio.run,
                                    args=(self.handle_response(client_socket),),
                                    daemon=True
                                ).start()
                    
                except KeyboardInterrupt:
                    shutil.rmtree('__pycache__', ignore_errors=True)
                    PrintLine(text='Server offline')
                    break
            
    def run(self, route: str, port: int, host: str):
        self.route, self.port, self.host = route, port, host
        self.create_server()