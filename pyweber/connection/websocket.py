import json
import inspect
import asyncio
import ssl
import websockets as ws
from threading import Thread
from websockets.sync.server import serve
from pyweber.pyweber.pyweber import Pyweber
from pyweber.models.ws_message import wsMessage
from pyweber.core.events import EventConstrutor
from pyweber.utils.utils import PrintLine, Colors
from pyweber.connection.session import sessions, Session

class WsServer:
    def __init__(self, host: str, port: int, use_ssl: bool, cert_file: str, key_file: str):
        self.host: str = host
        self.port: int = port
        self.app: Pyweber = None
        self.ws_connections: set[ws.server.ServerConnection] = set()
        self.color_red = Colors.RED
        self.color_reset = Colors.RESET
        self.use_ssl = use_ssl
        self.cert_file = cert_file
        self.key_file = key_file
        self.ssl_context = None

        if self.use_ssl in [True, 1, 'True', 'true'] and self.cert_file and self.key_file:
            self.ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            try:
                self.ssl_context.load_cert_chain(certfile=self.cert_file, keyfile=self.key_file)
            except Exception as e:
                PrintLine(f"{Colors.RED}WebSocket SSL configuration failed: {e}{Colors.RESET}")
                self.use_ssl = False
    
    def ws_handler(self, websocket: ws.server.ServerConnection):
        try:
            for message in websocket:
                message = wsMessage(raw_message=json.loads(message), app=self.app)
                if not message.session_id or message.session_id not in sessions.all_sessions:
                    websocket.id = message.session_id or str(websocket.id)
                    sessions.add_session(
                        session_id=websocket.id,
                        Session=Session(
                            template=message.template,
                            window=message.window
                        )
                    )
                    self.ws_connections.add(websocket)
                    websocket.send(json.dumps({'setSessionId': websocket.id}))
                
                if message.type and message.event_ref:
                    sessions.get_session(session_id=message.session_id).template = message.template
                    sessions.get_session(session_id=message.session_id).window = message.window
                    self.ws_message(message=message)
        
        except Exception as e:
            PrintLine(f'Error [ws]: {self.color_red}{e}{self.color_reset}')

        finally:
            self.ws_connections.discard(websocket)
            sessions.remove_session(session_id=websocket.id)
    
    def ws_message(self, message: wsMessage):
        event_handler = EventConstrutor(
            ws_message=message,
            ws_update=self.send_message,
            ws_reload=self.send_reload
        ).build_event

        if message.event_ref == 'document':
            if event_handler.element:
                event_id = event_handler.element.events.__dict__.get(f'on{message.type}')
                template_events = sessions.get_session(session_id=message.session_id).template.events
                
                if event_id and event_id in template_events:
                    handler = template_events.get(event_id)

                    if inspect.iscoroutinefunction(handler):
                        Thread(target=asyncio.run, args=(handler(event_handler),), daemon=True).start()
                    
                    else:
                        Thread(target=handler, args=(event_handler,), daemon=True).start()
        
        self.send_message(session_id=event_handler.session_id)
    
    def send_message(self, session_id: str):
        try:
            ws_conn = next((ws for ws in self.ws_connections if ws.id == session_id), None)

            if ws_conn:
                data = {
                    'template': sessions.get_session(ws_conn.id).template.build_html(),
                    'window_events': sessions.get_session(ws_conn.id).window.get_all_event_ids
                }

                ws_conn.send(json.dumps(data, ensure_ascii=False, indent=4))
        
        except Exception as e:
            PrintLine(f'Error sending message: {e}')
            return
    
    def send_reload(self, session_id: str = None):
        try:
            if session_id:
                ws_conn = next((ws for ws in self.ws_connections if ws.id == session_id), None)
                if ws_conn:
                    ws_conn.send('reload')
                    return
            
            for ws_conn in self.ws_connections:
                ws_conn.send('reload')

        except Exception as e:
            PrintLine(f'Error sending reload: {e}')
            return

    def ws_start(self):
        try:
            if self.use_ssl in [True, 1, 'True', 'true'] and self.ssl_context:
                with serve(self.ws_handler, self.host, self.port, ssl=self.ssl_context) as server:
                    server.serve_forever()
            else:
                with serve(self.ws_handler, self.host, self.port) as server:
                    server.serve_forever()
                
        except OSError as e:
            PrintLine(f"{Colors.RED}WebSocket server error: {e}{Colors.RESET}")
        except Exception as e:
            PrintLine(f"{Colors.RED}Unexpected error in WebSocket server: {e}{Colors.RESET}")