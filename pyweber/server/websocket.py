import websockets as ws
import asyncio
import json
from base64 import b64decode, b64encode
from pyweber.router.router import Router
from pyweber.utils.events import EventConstrutor
from pyweber.core.template import Template
from pyweber.core.elements import Element
from pyweber.utils.exceptions import RouteNotFoundError

class websockets:
    def __init__(self, host: str = 'localhost', port: int = 8765):
        self.__websocket_clients: set[ws.WebSocketClientProtocol] = set()
        self.port, self.host = port, host
        self.router: Router = None
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
    
    async def send_reload(self):
        if self.__websocket_clients:
            for client in self.__websocket_clients:
                try:
                    if client.open:
                        await client.send('reload')

                except Exception as e:
                    print(f'Erro ao actualizar cliente: {e}')
    
    async def ws_handler(self, websocket: ws.WebSocketClientProtocol, _):
        self.__websocket_clients.add(websocket)

        try:
            async for message in websocket:
                await self.handle_message(message, websocket)
        
        finally:
            self.__websocket_clients.remove(websocket)
    
    async def handle_message(self, message: str, websocket: ws.WebSocketClientProtocol):
        """Processa uma mensagem recebida do navegador."""
        try:
            event_handler = WsManager(event=json.loads(message), router=self.router).event_handler()

            if event_handler.element:
                event_id = event_handler.element.events.__dict__.get(f'on{event_handler.event_type}', None)
                template = event_handler.template

                if event_id:
                    if event_id in template.events:
                        try:
                            template.events.get(event_id)(event_handler)
                            new_html = b64encode(template.build_html().encode('utf-8')).decode('utf-8')
                            await websocket.send(json.dumps({'template': new_html}, ensure_ascii=False, indent=4))
                        
                        except Exception as e:
                            await websocket.send(json.dumps({'Error': str(e)}))
        
        except json.JSONDecodeError:
            print(f"Mensagem inválida recebida: {message}")
    
    async def ws_start(self):
        try:
            async with ws.serve(self.ws_handler, self.host, self.port):
                await asyncio.Future()
        except:
            pass

class WsManager:
    def __init__(self, event: dict[str, (str, int, dict, float)], router: Router):
        self.__event = event
        self.__router = router
    
    def update_template(self):
        try:
            html = b64decode(self.__event['template']).decode()
            values = json.loads(b64decode(self.__event['values']).decode())
            last_template = self.__router.get_template(route=self.__event['route'])

            new_element = last_template.parse_html(html=html)
            self.insert_values(values=values, element=new_element)
            last_template.root = new_element
        
        except RouteNotFoundError:
            last_template = self.__router.page_not_found

        return last_template
    
    def insert_values(self, values: dict[str, None], element: Element):
        element.value = values.get(element.uuid, None)

        for child in element.childs:
            self.insert_values(values, child)
    
    def update_event(self, event: dict[str, (str, dict, list)], template: Template):
        event['template'] = template
        return event
    
    def event_handler(self):
        return EventConstrutor(
            event=self.update_event(
                event=self.__event,
                template=self.update_template()
            )
        ).build_event