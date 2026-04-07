import socket
import ssl
import os
import shutil
import re
import asyncio

from typing import Union, Any
from concurrent.futures import ThreadPoolExecutor

from pyweber.pyweber.pyweber import Pyweber
from pyweber.utils.utils import Colors, PrintLine
from pyweber.models.request import Request, ClientInfo
from pyweber.connection.websocket import WebsocketUpgrade, WebsocketServer
from pyweber.connection.selector import IOSelector

class HttpServer: # pragma: no cover
    def __init__(self, *args, **kwargs):
        self.port: int = None
        self.host: str = None
        self.route: str = None
        self.mobile: bool = False
        self.timeout: float = None
        self.ssl_context: ssl.SSLContext = None
        self.__app: Pyweber = None
        self._pool = ThreadPoolExecutor(max_workers=200)

    @property
    def app(self): return self.__app

    @app.setter
    def app(self, value):
        self.__app = value

    async def send_data(self, client: Union[socket.socket, ssl.SSLSocket], data: bytes):
        client.sendall(data)

    def setup_ssl(self, cert_file: str, key_file: str):
        context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        context.load_cert_chain(certfile=cert_file, keyfile=key_file)
        self.ssl_context = context

        PrintLine(
            text=f"{Colors.GREEN}SSL configuration successful{Colors.RESET}"
        )

    async def read_data(self, client, length: int):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, client.recv, length)

    async def process_request(self, client: Union[socket.socket, ssl.SSLSocket]):
        try:
            request_data = bytearray()
            async with asyncio.timeout(self.timeout):
                while b'\r\n\r\n' not in request_data:
                    chunk = await self.read_data(client, 4096)
                    if not chunk: break
                    request_data.extend(chunk)

            header_bytes, _, body_start = request_data.partition(b'\r\n\r\n')
            header_text = header_bytes.decode('iso-8859-1')

            content_length = 0
            content_match = re.search(r"Content-Length: (\d+)", header_text, re.IGNORECASE)
            if content_match:
                content_length = int(content_match.group(1))


            body = bytearray(body_start)
            async with asyncio.timeout(self.timeout):
                while len(body) < content_length:
                    remaining = content_length - len(body)

                    chunk = await self.read_data(client, remaining)
                    if not chunk:
                        break
                    body.extend(chunk)

            return header_bytes, bytes(body)

        except (asyncio.TimeoutError, TimeoutError):
            PrintLine(text="Request timeout — client too slow or connection hung", level="WARNING")
            return b'', b''

    async def handle_client(self, client: Union[socket.socket, ssl.SSLSocket]):
        try:
            headers, body = await self.process_request(client)

            client_details = client.getpeername()
            client_info = ClientInfo(
                host=client_details[0] or 'unknown',
                port=client_details[-1] or 0
            )

            if not headers:
                client.close()
                return

            request = Request(
                headers=headers.decode('iso-8859-1'),
                body=body,
                client_info=client_info
            )

            if 'Connection: Upgrade' in request.raw_headers:
                upgrade = WebsocketUpgrade(headers=headers)
                upgrade_response = upgrade.upgrade_response.encode('utf-8')

                client.setblocking(False)
                ws_connection = WebsocketServer(client)

                await self.send_data(client, upgrade_response)
                await self.app.ws_server.connect_wsgi(ws_connection=ws_connection)

            else:
                response = await self.app.get_response(request)
                await self.send_data(client, response.build_response)

        except TypeError:
            pass
        except Exception as e:
            PrintLine(f'Server Error: {e}', level='ERROR')
            raise e

        finally:
            client.close()

    def start_server(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_server:
            client_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            client_server.settimeout(self.timeout)

            try:
                client_server.bind((self.host, self.port))
                client_server.listen(socket.SOMAXCONN)
                protocol = 'https' if self.ssl_context else 'http'

                public_url = f"Server online in {Colors.GREEN}{protocol}://{self.host if self.host != '0.0.0.0' else '127.0.0.1'}:{self.port}{self.route}{Colors.RESET}"
                local_url = f"{Colors.GREEN}{protocol}://{self.get_local_ip()}:{self.port}{self.route}{Colors.RESET}"

                if self.host not in ['localhost', '127.0.0.1']:
                    PrintLine(f"{public_url} or {local_url}")
                else:
                    PrintLine(public_url)

                if self.mobile:
                    self.generate_qrcode(local_url)

                selector = IOSelector()
                selector.register(client_server)

                try:
                    while True:
                        try:
                            ready = selector.select(timeout=1)

                            for sock in ready:
                                if sock is client_server:
                                    client, addr = client_server.accept()

                                    if self.ssl_context:
                                        try:
                                            client = self.ssl_context.wrap_socket(
                                                client,
                                                server_side=True
                                            )

                                        except Exception as error:
                                            PrintLine(f"SSL configuration failed {error}", level='ERROR')
                                            client.close()
                                            continue

                                    self._pool.submit(asyncio.run, self.handle_client(client))

                        except KeyboardInterrupt:
                            self.clear_cache(path='.')
                            PrintLine(text='Server offline')
                            break

                        except OSError:
                            continue

                except KeyboardInterrupt:
                    pass

                finally:
                    selector.close()

            except OSError as e:
                PrintLine(text=f'Error to running server: {e}', level='ERROR')
                raise e
            finally:
                client_server.close()

    def run(
        self,
        host: str = 'localhost',
        port: int = '8800',
        route: str = '/',
        cert_file: str = None,
        key_file: str = None,
        timeout: float = 30,
        mobile: bool = False
    ):
        self.host = host
        self.port = port
        self.route = route
        self.timeout = timeout
        self.mobile = mobile

        if key_file and cert_file:
            self.setup_ssl(cert_file, key_file)

        try:
            self.start_server()
        except KeyboardInterrupt:
            self.clear_cache()
            PrintLine('Server offline')

    def clear_cache(self, path: str = '.'):
        for root, folders, files in os.walk(path):
            if any(p in root for p in ['__pycache__', 'tests/config', '.pyweber']):
                shutil.rmtree(root, ignore_errors=True)

    def get_local_ip(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        try:
            s.connect(('8.8.8.8', 80))
            local_ip = s.getsockname()[0]
        finally:
            s.close()

        return local_ip

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
