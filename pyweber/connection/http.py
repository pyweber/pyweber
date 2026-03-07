import asyncio
import ssl
import re
import os
import shutil
from typing import TYPE_CHECKING
import socket

from pyweber.pyweber.pyweber import Pyweber
from pyweber.models.request import Request, ClientInfo
from pyweber.utils.utils import PrintLine, Colors
from pyweber.connection.websocket import WebsocketUpgrade, WebsocketServer

if TYPE_CHECKING: # pragma: no cover
    from pyweber.connection.websocket import TaskManager


class HttpServer: # pragma: no cover

    def __init__(self):
        self.route = None
        self.port = None
        self.host = None
        self.ssl_context = None
        self.task_manager: 'TaskManager' = None
        self.__app: Pyweber = None

    @property
    def app(self):
        return self.__app

    @app.setter
    def app(self, value: Pyweber):
        self.__app = value

    # ---------------- SSL ---------------- #

    def setup_ssl(self, cert_file: str, key_file: str):
        context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        context.load_cert_chain(certfile=cert_file, keyfile=key_file)
        self.ssl_context = context

        PrintLine(
            text=f"{Colors.GREEN}SSL configuration successful{Colors.RESET}"
        )

    # ---------------- HTTP PROCESS ---------------- #

    async def process_request(self, reader: asyncio.StreamReader):

        request_data = bytearray()

        while b'\r\n\r\n' not in request_data:
            chunk = await reader.read(4096)
            if not chunk:
                break
            request_data.extend(chunk)

        header_bytes, _, body_start = request_data.partition(b'\r\n\r\n')
        header_text = header_bytes.decode('iso-8859-1')

        content_length = 0
        content_match = re.search(r"Content-Length: (\d+)", header_text, re.IGNORECASE)

        if content_match:
            content_length = int(content_match.group(1))

        body = bytearray(body_start)

        while len(body) < content_length:
            remaining = content_length - len(body)
            chunk = await reader.read(remaining)
            if not chunk:
                break
            body.extend(chunk)

        return header_bytes, bytes(body)

    # ---------------- CLIENT HANDLER ---------------- #

    async def handle_client(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter
    ):
        try:
            headers, body = await self.process_request(reader)

            peer = writer.get_extra_info("peername")
            client_info = ClientInfo(
                host=peer[0] if peer else "unknown",
                port=peer[1] if peer else 0
            )

            if not headers:
                writer.close()
                await writer.wait_closed()
                return

            request = Request(
                headers=headers.decode('iso-8859-1'),
                body=body,
                client_info=client_info
            )

            # -------- WebSocket Upgrade -------- #

            if 'Connection: Upgrade' in request.raw_headers:
                upgrade = WebsocketUpgrade(headers=headers)

                writer.write(upgrade.upgrade_response.encode('utf-8'))
                await writer.drain()

                ws_connection = WebsocketServer(reader, writer)

                await self.app.ws_server.connect_wsgi(
                    ws_connection=ws_connection
                )

            else:
                response = await self.app.get_response(request=request)
                writer.write(response.build_response)
                await writer.drain()
        
        except TypeError:
            pass

        except Exception as e:
            PrintLine(text=f"Server error: {e}", level="ERROR")

        finally:
            try:
                writer.close()
                await writer.wait_closed()
            except Exception:
                pass

    # ---------------- RUN SERVER ---------------- #

    async def start_server(self):

        server = await asyncio.start_server(
            self.handle_client,
            self.host,
            self.port,
            ssl=self.ssl_context
        )

        protocol = 'https' if self.ssl_context else 'http'
        public_url = f"{protocol}://{self.host if self.host != '0.0.0.0' else '127.0.0.1'}:{self.port}{self.route}"
        local_url = f"{protocol}://{self.get_local_ip()}:{self.port}{self.route}"

        if self.host not in ['localhost', '127.0.0.1']:
            PrintLine(
                text=f"Server online in {Colors.GREEN}{public_url}{Colors.RESET} or {Colors.GREEN}{local_url}{Colors.RESET}"
            )
            self.generate_qrcode(text=local_url)
        else:
            PrintLine(
                text=f"Server online in {Colors.GREEN}{public_url}{Colors.RESET}"
            )

        async with server:
            await server.serve_forever()
    
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
    

    def run(
        self,
        host: str = 'localhost',
        port: int = 8800,
        route: str = '/',
        cert_file: str = None,
        key_file: str = None
    ):
        self.host = host
        self.port = port
        self.route = route

        if cert_file and key_file:
            self.setup_ssl(cert_file, key_file)

        try:
            asyncio.run(self.start_server())
        except KeyboardInterrupt:
            self.clear_cache('.')
            PrintLine(text="Server offline")

    # ---------------- CLEANUP ---------------- #

    def clear_cache(self, path: str = '.'):
        for root, folders, files in os.walk(path):
            if any(p in root for p in ['__pycache__', 'tests/config', '.pyweber']):
                shutil.rmtree(root, ignore_errors=True)