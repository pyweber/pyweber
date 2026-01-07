import socket
import select
import re
import os
import ssl
import shutil
import asyncio
from threading import Thread
from typing import TYPE_CHECKING

from pyweber.pyweber.pyweber import Pyweber
from pyweber.models.request import Request, ClientInfo
from pyweber.utils.utils import PrintLine, Colors
from pyweber.connection.websocket import WebsocketUpgrade, WebsocketServer


if TYPE_CHECKING: # pragma: no cover
    from pyweber.connection.websocket import TaskManager

class HttpServer: # pragma: no cover
    def __init__(self):
        self.connections: list[socket.socket] = []
        self.route, self.port, self.host = None, None, None
        self.current_directory = os.path.abspath(__file__)
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
            headers, body = await self.process_request(client=client)
            client_info = client.getpeername()

            if headers:
                request = Request(
                    headers=headers.decode('iso-8859-1'),
                    body=body,
                    client_info=ClientInfo(
                        host=client_info[0],
                        port=client_info[-1]
                    )
                )

                if 'Connection: Upgrade' in request.raw_headers:
                    upgrade_connection = WebsocketUpgrade(headers=headers)
                    ws_connection = WebsocketServer(connection=client)

                    client.sendall(upgrade_connection.upgrade_response.encode('utf-8'))
                    
                    await self.app.ws_server.connect_wsgi(ws_connection=ws_connection)

                else:
                    response = await self.app.get_response(request=request)
                    client.sendall(response.build_response)
        
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
                    self.generate_qrcode(text=local_url)

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
                        self.clear_cache(path='.')
                        PrintLine(text='Server offline')
                        break
        
            except OSError as e:
                PrintLine(text=f'Error to running server: {e}', level='ERROR')
                raise e
            
            except Exception as e:
                PrintLine(text=f'Error [server] 1: {e}', level='ERROR')
                raise e
    
    def generate_qrcode(self, text: str):
        import qrcode

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4
        )

        qr.add_data(data=text)
        qr.make(fit=True)

        PrintLine(text='Or connect using qrcode bellow:', level='INFO')
        qr.print_ascii()
    
    def clear_cache(self, path: str = '.'):
        for root, folders, files in os.walk(top=path):
            if any(p in root for p in ['__pycache__', 'tests/config', '.pyweber']):
                shutil.rmtree(path=root, ignore_errors=True)
            
    def run(self, route: str, port: int, host: str, cert_file: str, key_file: str):
        self.route, self.port, self.host = route, port, host

        if cert_file and key_file:
            self.setup_ssl(cert_file, key_file)
        
        self.create_server()