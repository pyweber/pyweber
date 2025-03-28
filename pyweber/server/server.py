import socket
import select
import sys
import os
import shutil
import subprocess
from uuid import uuid4
from threading import Thread
from pyweber.router.router import Router
from pyweber.router.request import Request
from pyweber.utils.utils import print_line, Colors

class Server:
    def __init__(self):
        self.connections: list[socket.socket] = []
        self.route, self.port, self.host = None, None, None
        self.sessions: list[str] = []
        self.current_directory = os.path.abspath(__file__)
    
    @property
    def router(self):
        return self.__router
    
    @router.setter
    def router(self, value: Router):
        self.__router = value
    
    def update_router(self, router: Router):
        print_line(text='♻  Updating router on pyweber server...')
        self.router = router

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
    
    def create_server(self, restart: bool = False):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_server:
            client_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            try:
                client_server.bind((self.host, self.port))
                client_server.listen(5)
                print_line(text=f'New server running in {self.get_pid(port=self.port)[-1]}')

            except OSError as e:
                print_line(text=f'Error to running server')
                return
            
            except:
                print_line(text=f'Error [server] 1: {e}')
            
            if not restart:
                url = f'http://{self.host if self.host != '0.0.0.0' else '127.0.0.1'}:{self.port}{self.route}'
                print_line(text=f'Server online in {Colors.GREEN.value}{url}{Colors.RESET.value}')
            
            session_id = str(uuid4())
            self.sessions.append(session_id)

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
                                    target=self.handle_response,
                                    args=(client_socket, session_id),
                                    daemon=True
                                ).start()
                    
                except KeyboardInterrupt:
                    shutil.rmtree('__pycache__', ignore_errors=True)
                    print_line(text='Server offline')
                    break
    
    def get_pid(self, port: int):
        listening_pid: list[int] = []

        try:
            if sys.platform != 'win32':
                result = subprocess.check_output(['lsof', '-t', '-i', f':{port}']).decode('utf-8').strip().split('\n')

                for res in result:
                    listening_pid.append(int(result))
            else:
                result = subprocess.check_output(
                    ['netstat', '-ano', '|', 'findstr', f':{port}'],
                    shell=True
                ).decode('utf-8').strip().split('\n')

                for res in result:
                    if 'LISTENING' in res:
                        listening_pid.append(int(res.strip().split()[-1]))

            return listening_pid
        
        except:
            return listening_pid
    
    def kill_process(self, pids: list[int]):
        try:
            for pid in pids:
                if sys.platform != 'win32':
                    command = ['kill', '-9', str(pid)]
                else:
                    command = ['taskkill', '/PID', str(pid), '/F']
                
                subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                print_line(text=f'♻  Process with pid {pid} finalized')
            
            return True
        
        except:
            return False
            
    def run(self, route: str, port: int, host: str):
        self.route, self.port, self.host = route, port, host
        self.create_server()