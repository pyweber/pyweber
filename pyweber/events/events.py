from pyweber.elements.elements import Element

class EventData:
    def __init__(self, event_data: dict[str, int]):
        self.clientX = event_data.get('clientX', None)
        self.clientY = event_data.get('clientY', None)
        self.timestamp = event_data.get('timestamp', None)
    
    def __repr__(self):
        return f'EventData(clientX: {self.clientX}, clientY: {self.clientY}, timestamp: {self.timestamp})'

class EventHandler:
    def __init__(self, event_type: str, route: str, element: Element, event_data: EventData):
        self.event_type = event_type
        self.route = route
        self.element = element
        self.event_data = event_data
    
    def __repr__(self):
        return f'EventHandler(event_type: {self.event_type}, route: {self.route}, element: Element(), event_data: EventData())'

class EventConstrutor:
    def __init__(self, event: dict[str, None]):
        self.__event = event
    
    @property
    def __build_element(self):
        return Element.from_json(self.__event['element'])
    
    @property
    def build_event(self):
        return EventHandler(
            event_type=self.__event['type'],
            route=self.__event['route'],
            element=self.__build_element,
            event_data=EventData(
                event_data=self.__event['event_data']
            )
        )