import uuid as UUID
from pyweber.utils.types import Events, EventType

class Element:
    def __init__(
        self,
        name: str,
        id: str = None,
        class_name: str = None,
        content: str = None,
        value: str = None,
        attrs: dict[str, str] = None,
        parent: 'Element' = None,
        childs: list['Element'] = None,
        events: Events = None,
        uuid: str = None,
    ):
        self.name = name
        self.id = id
        self.uuid = uuid or str(UUID.uuid4())
        self.class_name = class_name
        self.content = content
        self.value = value
        self.attrs = attrs if attrs else {}
        self.parent = parent
        self.childs = childs if childs else []
        self.__events = events if events else Events()
    
    @property
    def events(self):
        return self.__events
    
    @events.setter
    def events(self, value: Events):
        if not isinstance(value, Events):
            raise ValueError('The value needs to be an instance Events')
        
        self.__events = value
    
    def add_event(self, event_type: EventType, event: callable):
        """Adds an event listener to the element."""
        if event_type not in EventType:
            raise ValueError(f'EventType {event_type} is invalid')
        
        if not callable(event):
            raise TypeError(f'The event must be a callable function, but got {type(event)}')
        
        setattr(self.__events, event_type.value, event)
    
    def remove_event(self, event_type: EventType):
        """Removes an event listener from the element."""
        if event_type not in EventType:
            raise ValueError(f'EventType {event_type} is invalid')
        
        setattr(self.__events, event_type.value, None)

    def __repr__(self):
        return f"Element(name={self.name}, id={self.id}, uuid={self.uuid}, class_name={self.class_name}, content={self.content}, attributes={self.attrs}, childs={len(self.childs)})"