import json
from typing import TYPE_CHECKING, Union, List
from pyweber.connection.session import sessions
from pyweber.core.element import Element
from pyweber.models.file import File
from pyweber.models.file import Field
from pyweber.utils.utils import PrintLine

if TYPE_CHECKING:
    from pyweber.pyweber.pyweber import Pyweber
    from pyweber.connection.websocket import WebSocket

class wsMessage: # pragma: no cover
    def __init__(self, raw_message: dict[str, (str, float)], app, ws: 'WebSocket'):
        self.ws = ws
        self.__app = app
        self.__raw_message = raw_message
        self.__raw_window: dict[str, (int, str, float)] = self.get_raw_window()
        self.__values = self.get_form_values()
        self.route: str = self.get_value(key='route')
        self.type: str = self.get_value(key='type')
        self.event_ref: str = self.get_value(key='event_ref')
        self.target_uuid: str = self.get_value(key='target_uuid')
        self.event_data: dict[str, int] = self.get_value(key='event_data') or {}
        self.session_id: str = self.get_value(key='sessionId')
        self.window_event: str = self.get_value(key='window_event')
        self.template = self.get_template()
        self.window = self.get_window()
        
    @property
    def window_response(self) -> dict[str, (str, int)]:
        return self.__raw_message.get('window_response', {})
    
    def get_value(self, key: str):
        return self.__raw_message.get(key, None)
    
    async def get_template(self):
        self.__app: 'Pyweber' = self.__app
        if self.session_id in sessions.all_sessions:
            session_template = sessions.get_session(session_id=self.session_id).template
        else:
            session_template = await self.__app.clone_template(route=self.route)

        if self.get_value(key='template'):
            session_template.root = session_template.parse_html(html=self.get_value('template'))
            self.insert_values(element=session_template.root)
        
        return session_template
    
    def get_window(self):
        from pyweber.core.window import Screen, Location, Orientation, LocalStorage, SessionStorage
        from pyweber.core.window import window

        window._Window__ws = self.ws
        window.session_id = self.session_id
        window.width = self.get_window_values(key='width') or 0
        window.height = self.get_window_values(key='height') or 0
        window.inner_width = self.get_window_values(key='innerWidth') or 0
        window.inner_height = self.get_window_values(key='innerHeight') or 0
        window.scroll_x = self.get_window_values(key='scrollX') or 0
        window.scroll_y = self.get_window_values(key='scrollY') or 0
        window.screen = Screen(
            width=self.get_window_values(key='screen').get('width', None),
            height=self.get_window_values(key='screen').get('height', None),
            colorDepth=self.get_window_values(key='screen').get('colorDepth', None),
            pixelDepth=self.get_window_values(key='screen').get('pixelDepth', None),
            screenX=self.get_window_values(key='screen').get('screenX', None),
            screenY=self.get_window_values(key='screen').get('screenY', None),
            orientation=Orientation(
                angle=self.get_window_values(key='screen').get('orientation', {}).get('angle', None),
                type=self.get_window_values(key='screen').get('orientation', {}).get('type', None),
                on_change=self.get_window_values(key='screen').get('orientation', {}).get('on_change', None),
            )
        )
        window.location = Location(
            host=self.get_window_values(key='location').get('host', None),
            url=self.get_window_values(key='location').get('href', None),
            protocol=self.get_window_values(key='location').get('protocol', None),
            route=self.get_window_values(key='location').get('pathname', None),
            origin=self.get_window_values(key='location').get('origin', None),
        )
        window.session_storage = SessionStorage(
            data=json.loads(self.get_window_values(key='sessionStorage') or "{}"),
            session_id=self.session_id,
            ws=self.ws
        )
        window.local_storage = LocalStorage(
            data=json.loads(self.get_window_values(key='localStorage') or "{}"),
            session_id=self.session_id,
            ws=self.ws
        )

        return window
    
    def get_form_values(self) -> dict[str, (str, int, float)]:
        return json.loads(self.get_value(key='values') or "{}") or {}
    
    def get_raw_window(self):
        return json.loads(self.get_value(key='window_data') or "{}")

    def get_window_values(self, key: str):
        return self.__raw_window.get(key, {})
    
    def insert_values(self, element: Element):
        values: Union[List[dict[str, Union[str, List[int]]]], str] = self.__values.get(element.uuid, None)
        if element.tag == 'input' and element.attrs.get('type') == 'file':

            element.files.extend([
                File(
                    field=Field(
                        name=None,
                        filename=value.get('name'),
                        content_type=value.get('content_type'),
                        value=bytes(value.get('content'))
                    )
                ) for value in values if value
            ])

            element.value = ';'.join([value.get('name') for value in values if value]) or None
            
        else:
            element.value = values

        if element.childs:
            for child in element.childs:
                self.insert_values(element=child)