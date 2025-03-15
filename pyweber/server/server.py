import socket
import select
from uuid import uuid4
from threading import Thread
from pyweber.router.router import Router
from pyweber.router.request import Request

class Server:
    def __init__(self, router: Router):
        self.router = router
        self.connections: list[socket.socket] = []
        self.route, self.port, self.host = None, None, None
        self.sessions: list[str] = []
    
    def handle_response(self, client: socket.socket, session_id: str):
        try:
            request = client.recv(1024).decode()

            if request:
                client.sendall(self.router.get_route(request=Request(raw_request=request)))
        
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

            url = f'http://{self.host if self.host != '0.0.0.0' else '127.0.0.1'}:{self.port}{self.route}'
            print(f'🌐 Servidor rodando em {url}')
            session_id = str(uuid4())
            self.sessions.append(session_id)

            while True:
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
            
    def run(self, route: str, port: int, host: str):
        self.route, self.port, self.host = route, port, host
        self.create_server()