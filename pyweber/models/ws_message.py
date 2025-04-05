import json
from pyweber.connection.session import sessions
from pyweber.pyweber.pyweber import Pyweber
from pyweber.core.element import Element
from pyweber.core.window import (
    Screen,
    Location,
    Orientation
)
class wsMessage:
    def __init__(self, raw_message: dict[str, (str, float)], app: Pyweber):
        self.__raw_message = raw_message
        self.__raw_window: dict[str, (int, str, float)] = self.get_raw_window()
        self.__values = self.get_form_values()
        self.__app = app
        self.route: str = self.get_value(key='route')
        self.type: str = self.get_value(key='type')
        self.event_ref: str = self.get_value(key='event_ref')
        self.target_uuid: str = self.get_value(key='target_uuid')
        self.event_data: dict[str, int] = self.get_value(key='event_data')
        self.session_id: str = self.get_value(key='sessionId')
        self.template = self.get_template()
        self.window = self.get_window()
    
    def get_value(self, key: str):
        return self.__raw_message.get(key, None)
    
    def get_template(self):
        if self.session_id in sessions.all_sessions:
            session_template = sessions.get_session(session_id=self.session_id).template
        else:
            session_template = self.__app.clone_template(route=self.route)

        if self.get_value(key='template'):
            session_template.root = session_template.parse_html(html=self.get_value('template'))
            self.insert_values(element=session_template.root)
        
        return session_template
    
    def get_window(self):
        window = self.__app.window

        window.width = self.get_window_values(key='width')
        window.height = self.get_window_values(key='height')
        window.inner_width = self.get_window_values(key='innerWidth')
        window.inner_height = self.get_window_values(key='innerHeight')
        window.scroll_x = self.get_window_values(key='scrollX')
        window.scroll_y = self.get_window_values(key='scrollY')
        window.screen = Screen(
            width=self.get_window_values(key='screen').get('width', None),
            height=self.get_window_values(key='screen').get('height', None),
            colorDepth=self.get_window_values(key='screen').get('colorDepth', None),
            pixelDepth=self.get_window_values(key='screen').get('pixelDepth', None),
            screenX=self.get_window_values(key='screen').get('screenX', None),
            screenY=self.get_window_values(key='screen').get('screenY', None),
            orientation=Orientation(
                angle=self.get_window_values(key='screen').get('orientation', None).get('angle', None),
                type=self.get_window_values(key='screen').get('orientation', None).get('type', None),
                on_change=self.get_window_values(key='screen').get('orientation', None).get('on_change', None),
            )
        )
        window.location = Location(
            host=self.get_window_values(key='location').get('host', None),
            url=self.get_window_values(key='location').get('href', None),
            protocol=self.get_window_values(key='location').get('protocol', None),
            route=self.get_window_values(key='location').get('pathname', None),
            origin=self.get_window_values(key='location').get('origin', None),
        )
        window.session_storage = json.loads(self.get_window_values(key='sessionStorage'))
        window.local_storage = json.loads(self.get_window_values(key='localStorage'))

        return window
    
    def get_form_values(self) -> dict[str, (str, int, float)]:
        return json.loads(self.get_value(key='values')) or {}
    
    def get_raw_window(self):
        return json.loads(self.get_value(key='window_data'))

    def get_window_values(self, key: str):
        return self.__raw_window.get(key, {})
    
    def insert_values(self, element: Element):
        element.value = self.__values.get(element.uuid, None)
        if element.childs:
            for child in element.childs:
                self.insert_values(element=child)