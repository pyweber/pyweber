import jwt
import socket
import select
import requests
from urllib.parse import urlparse
from uuid import uuid4
from datetime import timedelta, datetime, timezone
from threading import Thread
from pyweber.router.router import Router
from pyweber.utils.types import ContentTypes
from pyweber.utils.load import LoadStaticFiles
from pyweber.utils.exceptions import *
from pyweber.utils.types import HTTPStatusCode

class Server:
    def __init__(self, router: Router):
        self.router = router
        self.connections: list[socket.socket] = []
        self.route = None
        self.port = None
        self.host = None
        self.no_kill = True
        self.expiration_token: timedelta = timedelta(hours=1)
        self.sessions: list[str] = []
        self.__secret_key = None
    
    def create_new_token(self, session_id: str):
        expiration = datetime.now(tz=timezone.utc) + self.expiration_token
        pylaod = {
            'session_id': session_id,
            'exp': expiration
        }
        return jwt.encode(pylaod, self.__secret_key, algorithm='HS256')
    
    def validate_token(self, token: str):
        try:
            pyload = jwt.decode(token, self.__secret_key, algorithms=['HS256'])
            return pyload
        except jwt.ExpiredSignatureError:
            return 'expired'
        except jwt.InvalidTokenError:
            return 'invalid'
    
    def get_cookies(self, request: str):
        cookie_header = request.split('Cookie: ')[-1] if 'Cookie' in request else ''
        cookies = {cookie.split('=')[0]: cookie.split('=')[1] for cookie in cookie_header.split(';')} if cookie_header else {}
        return cookies.get('auth_token', None)
    
    def set_cookie(self, cookie_name: str, cookie_value: str):
        return f"Set-Cookie: {cookie_name}={cookie_value}; HttpOnly; Path=/; Secure; SameSite=Strict\r\n"

    def serve_file(self, request: str, session_id: str):
        route = request.split(' ')[1]
        content_type = ContentTypes.html
        token = self.get_cookies(request=request)

        try:
            token = None if token.strip() == str(None) else token.strip()
        
        except:
            token = None

        if token:
            pyload = self.validate_token(token=token)

            if pyload == 'invalid':
                return self.build_response(
                    request=request,
                    code=HTTPStatusCode.UNAUTHORIZED.value,
                    content=self.router.page_unauthorized.build_html(),
                    content_type=content_type
                )
            
            elif pyload == 'expired':
                token = self.create_new_token(session_id=session_id)

        else:
            token = self.create_new_token(session_id=session_id)
        
        cookie = self.set_cookie(cookie_name='auth_token', cookie_value=token)

        try:
            parsed_url = urlparse(url=route)
            path = parsed_url.path.strip()
            path_netloc = parsed_url.netloc
            
            if '.' in path:
                extension = path.split('.')[-1].lower().strip()
                if extension in ContentTypes.content_list():
                    content_type: ContentTypes = getattr(ContentTypes, extension, ContentTypes.html)
                
                if not path_netloc:
                    return self.build_response(
                        request=request,
                        code=HTTPStatusCode.OK.value,
                        content=LoadStaticFiles(path=route).load,
                        content_type=content_type,
                        cookies=cookie
                    )
                
                else:
                    ext_request = requests.request(method='GET', url=route)

                    if ext_request.status_code != 200:
                        return self.build_response(
                            request=request,
                            code=HTTPStatusCode.search_by_code(ext_request.status_code),
                            content='',
                            content_type=content_type,
                            cookies=cookie
                        )
                    
                    else:
                        return self.build_response(
                            request=request,
                            code=HTTPStatusCode.OK.value,
                            content=ext_request.content,
                            content_type=content_type,
                            cookies=cookie
                        )
            
            else:
                self.router.update()
                if self.router.exists(route) or self.router.is_redirected(route):
                    self.route = route

                    if self.router.is_redirected(route=route):
                        return self.build_response(
                            request=request,
                            code=f'{HTTPStatusCode.FOUND.value}\r\nLocation: {self.router.get_redirected_route(route)}',
                            content=self.router.get_route(route=route).build_html(),
                            content_type=content_type,
                            cookies=cookie
                        )

                    return self.build_response(
                        request=request,
                        code=HTTPStatusCode.OK.value,
                        content=self.router.get_route(route=route).build_html(),
                        content_type=content_type,
                        cookies=cookie
                    )

                return self.build_response(
                        request=request,
                        code=HTTPStatusCode.NOT_FOUND.value,
                        content=self.router.page_not_found.build_html(),
                        content_type=content_type,
                        cookies=cookie
                    )
            
        except FileNotFoundError:
            return self.build_response(
                request=request,
                code=HTTPStatusCode.NOT_FOUND.value,
                content='',
                content_type=content_type,
                cookies=cookie
            )

        except RouteNotFoundError:
            return self.build_response(
                request=request,
                code=HTTPStatusCode.NOT_FOUND.value,
                content=self.router.page_not_found.build_html(),
                content_type=content_type,
                cookies=cookie
            )

    def build_response(self, request: str, code: str, content: str | bytes, content_type: ContentTypes, cookies: str = None) -> bytes:
        file_content = content.encode() if not isinstance(content, bytes) else content
        response = (
            f'HTTP/1.1 {code}\r\n'
            f'Content-Type: {content_type.value}; charset=UTF-8\r\n'
            f'Content-Length: {len(file_content)}\r\n'
            f'Connection: close\r\n'
        )

        if cookies:
            response += cookies
        response += '\r\n'

        print_response = request.split('\n')[0].strip()
        print(f"{print_response} {code}")
        return response.encode() + file_content
    
    def handle_response(self, client: socket.socket, session_id: str):
        try:
            request = client.recv(1024).decode()

            if request:
                client.sendall(self.serve_file(request=request, session_id=session_id))
        
        except BlockingIOError:
            pass
        
        finally:
            if client in self.connections:
                self.connections.remove(client)
                self.sessions.remove(session_id)

            client.close()
    
    def create_server(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_server:
            try:
                client_server.bind((self.host, self.port))
                client_server.listen(5)
            
            except:
                pass

            url = f'http://{self.host}:{self.port}{self.route}'
            print(f'🌐 Servidor rodando em {url}')
            session_id = str(uuid4())
            self.sessions.append(session_id)

            while self.no_kill:
                try:
                    rlist, _, _ = select.select([client_server], [], [], 1)

                    for server in rlist:
                        if server is client_server:
                            client_socket, _ = client_server.accept()
                            self.connections.append(server)

                            Thread(target=self.handle_response, args=(client_socket, session_id), daemon=True).start()
                    
                except KeyboardInterrupt:
                    print('Servidor desligado')
                    break
            
    def run(self, route: str, port: int, host: str, secret_key: str):
        self.route, self.port, self.host, self.__secret_key = route, port, host, secret_key
        self.create_server()