from pyweber.core.template import Template, Element

class EventData:
    def __init__(self, event_data: dict[str, int]):
        self.clientX = event_data.get('clientX', None)
        self.clientY = event_data.get('clientY', None)
        self.key = event_data.get('key', None)
        self.deltaX = event_data.get('deltaX', None)
        self.deltaY = event_data.get('deltaY', None)
        self.touches = event_data.get('touches', None)
        self.timestamp = event_data.get('timestamp', None)

    def __repr__(self):
        return f'EventData(key: {self.key}, clientX: {self.clientX}, clientY: {self.clientY}, timestamp: {self.timestamp})'

class EventHandler:
    def __init__(self, event_type: str, route: str, element: Element, template: Template, event_data: EventData):
        self.event_type = event_type
        self.route = route
        self.element = element
        self.template = template
        self.event_data = event_data
    
    def __repr__(self):
        return f'EventHandler(event_type: {self.event_type}, route: {self.route}, element: Element(), template: Template(), event_data: EventData())'

class EventConstrutor:
    def __init__(self, event: dict[str, None]):
        self.__event = event
    
    @property
    def __template(self) -> Template:
        return self.__event['template']
    
    @property
    def __target_element(self) -> Element:
        return self.__template.getElementByUUID(
            element_uuid=self.__event['target_uuid']
        )
    
    @property
    def build_event(self):
        return EventHandler(
            event_type=self.__event['type'],
            route=self.__event['route'],
            element=self.__target_element,
            template=self.__template,
            event_data=EventData(
                event_data=self.__event['event_data']
            )
        )