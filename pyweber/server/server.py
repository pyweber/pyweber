import socket
import select
from threading import Thread
from pyweber.router.router import Router
from pyweber.content_type.content_types import ContentTypes
from pyweber.static_files.static_files import LoadStaticFiles
from pyweber.template_codes.template_codes import WS_CODE, PAGE_NOT_FOUND

class Server:
    def __init__(self, router: Router):
        self.router = router
        self.connections: list[socket.socket] = []
        self.route = '/'
        self.port = 8800
        self.reload = True
        self.host = 'localhost'
        self.no_kill = True
        self.server_running = False
        self.server_thread = None
    
    def add_template_code(self, template: str):
        if self.reload:
            return template.replace(
                '</body>',
                WS_CODE
            )
        
        return template
    
    def serve_file(self, request: str):
        route = request.split(' ')[1]
        content_type = ContentTypes.html

        try:
            if self.router.exists(route) or self.router.is_redirected(route):
                if self.router.is_redirected(route=route):
                    code = f"302 Found\r\nLocation: {self.router.get_redirected_route(route)}"

                else:
                    code: str = '200 OK'
                self.route = route
                html = self.add_template_code(
                    template=self.router.get_route(route=self.route).rebuild_html
                )
            
            elif '.' in route:
                extension = route.split('.')[-1].lower().strip()
                if extension in ContentTypes.content_list():
                    content_type: ContentTypes = getattr(ContentTypes, extension)

                html = LoadStaticFiles(route).load
                code: str = '200 OK'
            
            else:
                code: str = '404 Not Found'
                html = self.add_template_code(
                    template=PAGE_NOT_FOUND
                )
            
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

            self.server_running = True

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
            
    def run(self, route: str, port: int, reload: bool):
        self.route, self.port, self.reload = route, port, reload
        self.create_server()