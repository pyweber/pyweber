import websockets as ws
import asyncio
import json
from base64 import b64decode, b64encode
from pyweber.router.router import Router
from pyweber.utils.events import EventConstrutor
from pyweber.core.template import Template
from pyweber.core.element import Element
from pyweber.utils.exceptions import RouteNotFoundError
import inspect

class websockets:
    def __init__(self, host: str = 'localhost', port: int = 8765):
        self.__websocket_clients: set[ws.WebSocketClientProtocol] = set()
        self.__ws_client_protocol: ws.WebSocketClientProtocol = None
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
            self.event_handler = WsManager(
                event=json.loads(message),
                router=self.router,
                update_handler=self.update,
                loop=self.loop
            ).event_handler()
            self.__ws_client_protocol = websocket

            if self.event_handler.element:
                event_id = self.event_handler.element.events.__dict__.get(f'on{self.event_handler.event_type}', None)

                if event_id:
                    if event_id in self.event_handler.template.events:
                        handler = self.event_handler.template.events.get(event_id)

                        if inspect.iscoroutinefunction(handler):
                            asyncio.create_task(
                                handler(self.event_handler)
                            )
                        else:
                            handler(self.event_handler)

                        await self.update()
        
        except json.JSONDecodeError:
            print(f"Invalid message received: {message}")
    
    async def ws_start(self):
        try:
            async with ws.serve(self.ws_handler, self.host, self.port):
                await asyncio.Future()
        except:
            pass
    
    async def update(self):
        try:
            new_html = b64encode(self.event_handler.template.build_html().encode('utf-8')).decode('utf-8')
            await self.__ws_client_protocol.send(json.dumps({'template': new_html}, ensure_ascii=False, indent=4))
        
        except Exception as e:
            await self.__ws_client_protocol.send(json.dumps({'Error': str(e)}))

class WsManager:
    def __init__(
            self,
            event: dict[str, (str, int, dict, float)],
            router: Router,
            update_handler: callable,
            loop: asyncio.AbstractEventLoop
        ):
        self.__event = event
        self.__router = router
        self.__update_handler = update_handler
        self.__loop = loop
    
    def update_template(self):
        try:
            html = b64decode(self.__event['template']).decode()
            values = json.loads(b64decode(self.__event['values']).decode())
            last_template = self.__router.get_template(route=self.__event['route'])

            # Criar o novo elemento raiz
            new_element = last_template.parse_html(html=html)
            self.insert_values(values=values, element=new_element)
            self.update_template_reference(template=last_template, element=new_element)
            self.update_window()

            # Atualizar o template
            last_template.root = new_element

        except RouteNotFoundError:
            last_template = self.__router.page_not_found

        return last_template
    
    def update_window(self):
        window_dict: dict[str, dict[str, str]] = json.loads(b64decode(self.__event['window_data']))
        window = self.__router.window

        window.height = window_dict['height']
        window.width = window_dict['width']
        window.outer_height = window_dict['outerHeight']
        window.outer_width = window_dict['outerWidth']
        window.scroll_x = window_dict['scrollX']
        window.scroll_y = window_dict['scrollY']
        window.screen_x = window_dict['screenX']
        window.screen_y = window_dict['screenY']
        window.local_storage = json.loads(window_dict['localStorage'])
        window.session_storage = json.loads(window_dict['sessionStorage'])
        window.history = window_dict['history']
        window.navigator = window_dict['navigator']
        window.location = window_dict['location']
    
    def insert_values(self, values: dict[str, None], element: Element):
        element.value = values.get(element.uuid, None)

        for child in element.childs:
            self.insert_values(values, child)
    
    def update_event(self, event: dict[str, (str, dict, list)], template: Template):
        event['template'] = template
        event['update'] = self.__update_handler
        event['router'] = self.__router
        event['loop'] = self.__loop
        return event
    
    def update_template_reference(self, template: Template, element: Element):
        element.template = template

        for child in element.childs:
            child.template = template
    
    def event_handler(self):
        return EventConstrutor(
            event=self.update_event(
                event=self.__event,
                template=self.update_template()
            )
        ).build_event