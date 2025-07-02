import socket
import select
import re
import os
import ssl
import shutil
import asyncio
from threading import Thread
from pyweber.pyweber.pyweber import Pyweber
from pyweber.models.request import Request, ClientInfo
from pyweber.utils.utils import PrintLine, Colors
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from pyweber.connection.websocket import TaskManager

class HttpServer:
    def __init__(self, update_handler: Callable):
        self.connections: list[socket.socket] = []
        self.route, self.port, self.host = None, None, None
        self.current_directory = os.path.abspath(__file__)
        self.update_server = update_handler
        self.started = False
        self.ssl_context = None
        self.task_manager: 'TaskManager' = None

    @property
    def app(self):
        return self.__app
    
    @app.setter
    def app(self, value: Pyweber):
        self.__app = value
    
    def is_file_request(self, request: Request):
        return self.app.is_file_requested(route=request.path)
    
    def setup_ssl(self, cert_file: str, key_file: str):
        self.ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)

        try:
            self.ssl_context.load_cert_chain(certfile=cert_file, keyfile=key_file)
            PrintLine(text=f"{Colors.GREEN}SSL configuration successful{Colors.RESET}")
        except Exception as e:
            PrintLine(text=f"{Colors.RED}SSL configuration failed: {e}{Colors.RESET}", level='ERROR')
            self.ssl_context = None
    
    async def process_request(self, client: socket.socket) -> tuple[bytes, bytes]:
        request_data = b''

        while b'\r\n\r\n' not in request_data:
            chunk = client.recv(1024)

            if not chunk:
                break

            request_data += chunk
        
        header_bytes, _, body_start = request_data.partition(b'\r\n\r\n')
        header_text = header_bytes.decode('iso-8859-1')

        content_length = 0
        content_match = re.search(r"Content-Length: (\d+)", header_text, re.IGNORECASE)

        if content_match:
            content_length = int(content_match.group(1))
        
        body = body_start
        while len(body) < content_length:
            chunk = client.recv(4096)

            if not chunk:
                break

            body += chunk
        
        return header_bytes, body

    async def handle_response(self, client: socket.socket | ssl.SSLSocket):
        try:
            request_tuple = await self.process_request(client=client)
            client_info = client.getpeername()

            if request_tuple:
                request=Request(
                    headers=request_tuple[0].decode('iso-8859-1'),
                    body=request_tuple[-1],
                    client_info=ClientInfo(
                        host=client_info[0],
                        port=client_info[-1]
                    )
                )

                if request.path:
                    if self.started:
                        if not self.is_file_request(request):
                            self.update_server()
                    
                    response = await self.app.get_response(request=request)
                    client.sendall(response.build_response)

                    if not self.is_file_request(request):
                        self.started = True
        
        except BlockingIOError:
            pass

        except UnicodeDecodeError:
            PrintLine(
                text=f'Error [Server]: Protocol http incompatible, please use same http protocol for response and request',
                level='ERROR'
            )
        
        finally:
            if client in self.connections:
                self.connections.remove(client)

            client.close()
    
    def get_local_ip(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        try:
            s.connect(('8.8.8.8', 80))
            local_ip = s.getsockname()[0]
        finally:
            s.close()
        
        return local_ip
    
    def create_server(self, restart: bool = False):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_server:
            client_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            try:
                client_server.bind((self.host, self.port))
                client_server.listen(5)
                protocol = 'https' if self.ssl_context else 'http'

                if not restart:
                    public_url = f"{protocol}://{self.host if self.host != '0.0.0.0' else '127.0.0.1'}:{self.port}{self.route}"
                    local_url = f"{protocol}://{self.get_local_ip()}:{self.port}{self.route}"
                    PrintLine(
                        text=f"Server online in {Colors.GREEN}{public_url}{Colors.RESET} or {Colors.GREEN}{local_url}{Colors.RESET}"
                    )

                while True:
                    try:
                        rlist, _, _ = select.select([client_server], [], [], 1)

                        if not rlist:
                            continue

                        else:
                            for server in rlist:
                                if server is client_server:
                                    client_socket, _ = client_server.accept()
                                    if self.ssl_context:
                                        try:
                                            client_socket = self.ssl_context.wrap_socket(
                                                client_socket,
                                                server_side=True
                                            )
                                        except Exception as e:
                                            PrintLine(text=f"SSL Error: {e}", level='ERROR')
                                            client_socket.close()
                                            continue

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
        
            except OSError as e:
                PrintLine(text=f'Error to running server: {e}', level='ERROR')
                raise e
            
            except Exception as e:
                PrintLine(text=f'Error [server] 1: {e}', level='ERROR')
                raise e
            
    def run(self, route: str, port: int, host: str, cert_file: str, key_file: str):
        self.route, self.port, self.host = route, port, host

        if cert_file and key_file:
            self.setup_ssl(cert_file, key_file)
        
        self.create_server()