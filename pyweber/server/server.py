import socket
import select
import requests
from threading import Thread
from pyweber.router.router import Router
from pyweber.utils.types import ContentTypes
from pyweber.utils.load import LoadStaticFiles

class Server:
    def __init__(self, router: Router):
        self.router = router
        self.connections: list[socket.socket] = []
        self.route = None
        self.port = None
        self.host = None
        self.no_kill = True
    
    def serve_file(self, request: str):
        route = request.split(' ')[1]
        content_type = ContentTypes.html

        try:
            if '.' in route:
                if route.startswith('/'):
                    extension = route.split('.')[-1].lower().strip()
                    if extension in ContentTypes.content_list():
                        content_type: ContentTypes = getattr(ContentTypes, extension, ContentTypes.html)
                    
                    html = LoadStaticFiles(route).load
                    code: str = '200 OK'
                
                else:
                    ext_request = requests.request(method='get', url=route)

                    if ext_request.status_code != 200:
                        code = ext_request.status_code
                        html = ''
                    
                    else:
                        code: str = '200 OK'
                        html = ext_request.content
            
            else:
                if self.router.exists(route) or self.router.is_redirected(route):
                    if self.router.is_redirected(route=route):
                        code = f"302 Found\r\nLocation: {self.router.get_redirected_route(route)}"

                    else:
                        code: str = '200 OK'
                    
                else:
                    code: str = '404 Not Found'
                
                self.route = route
                html = self.router.get_route(route=route).build_html()
            
        except FileNotFoundError:
            code: str = '404 Not Found'
            html = ''
        
        file_content = html.encode() if not isinstance(html, bytes) else html

        response: str = f'HTTP/1.1 {code}\r\n'
        response += f'Content-Type: {content_type.value}; charset=UTF-8\r\n'
        response += f'Content-Length: {len(file_content)}\r\n'
        response += 'Connection: close\r\n'
        response += '\r\n'

        response_encoded = response.encode() + file_content

        print_response = request.split('\n')[0].strip()
        print(f"{print_response} {code}")

        return response_encoded
    
    def handle_response(self, client: socket.socket):
        try:
            request = client.recv(1024).decode()

            if request:
                client.sendall(self.serve_file(request=request))
        
        except BlockingIOError:
            pass
        
        finally:
            if client in self.connections:
                self.connections.remove(client)

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

            while self.no_kill:
                try:
                    rlist, _, _ = select.select([client_server], [], [], 1)

                    for server in rlist:
                        if server is client_server:
                            client_socket, _ = client_server.accept()
                            self.connections.append(server)

                            Thread(target=self.handle_response, args=(client_socket,), daemon=True).start()
                    
                except KeyboardInterrupt:
                    print('Servidor desligado')
                    break
            
    def run(self, route: str, port: int, host: str):
        self.route, self.port, self.host = route, port, host
        self.create_server()