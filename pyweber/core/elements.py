import uuid as UUID
from pyweber.utils.types import Events, EventType

class Element:

    def __init__(
        self,
        name: str,
        id: str = None,
        classes: list[str] = None,
        content: str = None,
        value: str = None,
        style: dict[str, str] = None,
        attrs: dict[str, str] = None,
        parent: 'Element' = None,
        childs: list['Element'] = None,
        events: Events = None,
        uuid: str = None,
        template = None
    ):
        self.__uuid = uuid or str(UUID.uuid4())
        self.__name = name
        self.__id = id
        self.__content = content
        self.__value = value
        self.__parent = parent
        self.__style = style if style else {}
        self.__attrs = attrs if attrs else {}
        self.__childs = childs if childs else []
        self.__classes = classes if classes else []
        self.__events = events if events else Events()
        self.__template = template
    
    @property
    def template(self):
        return self.__template
    
    @template.setter
    def template(self, template):
        self.__template = template
    
    # Name property
    @property
    def name(self) -> str:
        return self.__name

    @name.setter
    def name(self, value: str):
        if not isinstance(value, str):
            raise TypeError("Element name must be a string")
        if not value.strip():
            raise ValueError("Element name cannot be empty")
        self.__name = value

    # ID property
    @property
    def id(self) -> str:
        return self.__id

    @id.setter
    def id(self, value: str):
        if value is not None and not isinstance(value, str):
            raise TypeError("Element id must be a string")
        self.__id = value

    # UUID property
    @property
    def uuid(self) -> str:
        return self.__uuid

    @uuid.setter
    def uuid(self, value: str):
        if not isinstance(value, str):
            raise TypeError("UUID must be a string")
        if not value.strip():
            raise ValueError("UUID cannot be empty")

    @property
    def classes(self) -> list:
        return self.__classes

    @classes.setter
    def classes(self, value: str | list[str]):
        if value is None:
            self.__classes = []
        elif isinstance(value, str):
            # Converter string para lista, removendo espaços extras
            self.__classes = [cls for cls in value.split() if cls]
        elif isinstance(value, list):
            # Verificar se todos os itens são strings
            if not all(isinstance(cls, str) for cls in value):
                raise TypeError("All class names must be strings")
            self.__classes = value
        else:
            raise TypeError("Classes must be a string or list of strings")

    # Métodos auxiliares
    def add_class(self, class_name: str):
        """Add a class to the element."""
        if not isinstance(class_name, str):
            raise TypeError("Class name must be a string")
        if class_name and class_name not in self.__classes:
            self.__classes.append(class_name)

    def remove_class(self, class_name: str):
        """Remove a class from the element."""
        if not isinstance(class_name, str):
            raise TypeError("Class name must be a string")
        if class_name in self.__classes:
            self.__classes.remove(class_name)

    def has_class(self, class_name: str) -> bool:
        """Check if the element has a specific class."""
        if not isinstance(class_name, str):
            raise TypeError("Class name must be a string")
        return class_name in self.__classes

    def toggle_class(self, class_name: str):
        """Toggle a class on the element."""
        if not isinstance(class_name, str):
            raise TypeError("Class name must be a string")
        if class_name in self.__classes:
            self.__classes.remove(class_name)
        else:
            self.__classes.append(class_name)

    # Content property
    @property
    def content(self) -> str:
        return self.__content

    @content.setter
    def content(self, value):
        if value is None:
            self.__content = None
        else:
            # Converter automaticamente para string
            try:
                self.__content = str(value)
            except Exception as e:
                raise ValueError(f"Could not convert content to string: {e}")

    # Value property
    @property
    def value(self) -> str:
        return self.__value

    @value.setter
    def value(self, value):
        if value is None:
            self.__value = value
        else:
            # Converter automaticamente para string
            try:
                self.__value = str(value)
            except Exception as e:
                raise ValueError(f"Could not convert value to string: {e}")

    # Style property
    @property
    def style(self) -> dict:
        return self.__style

    @style.setter
    def style(self, value: dict[str, str]):
        if not isinstance(value, dict):
            raise TypeError("Style must be a dictionary")

        # Validate all keys and values are strings
        for k, v in value.items():
            if not isinstance(k, str) or not isinstance(v, str):
                raise TypeError("Style keys and values must be strings")

        self.__style = value

    # Method to set a single style property
    def set_style(self, key: str, value: str):
        if not isinstance(key, str):
            raise TypeError("Style key must be a string")
        if not isinstance(value, str):
            raise TypeError("Style value must be a string")

        self.__style[key] = value

    # Method to get a single style property
    def get_style(self, key: str, default=None):
        if not isinstance(key, str):
            raise TypeError("Style key must be a string")

        return self.__style.get(key, default)

    # Method to remove a style property
    def remove_style(self, key: str):
        if not isinstance(key, str):
            raise TypeError("Style key must be a string")

        if key in self.__style:
            del self.__style[key]

    # Attributes property
    @property
    def attrs(self) -> dict:
        return self.__attrs

    @attrs.setter
    def attrs(self, value: dict[str, (str, int, float)]):
        if not isinstance(value, dict):
            raise TypeError("Attributes must be a dictionary")

        # Validate all keys are strings
        for k, v in value.items():
            if not isinstance(k, str):
                raise TypeError("Attribute keys must be strings")
            if v is not None and not isinstance(v, str):
                raise TypeError("Attribute values must be strings or None")

        self.__attrs = value

    # Method to set a single attribute
    def set_attr(self, key: str, value: str):
        if not isinstance(key, str):
            raise TypeError("Attribute key must be a string")
        if value is not None and not isinstance(value, str):
            raise TypeError("Attribute value must be a string or None")

        self.__attrs[key] = value

    # Method to get a single attribute
    def get_attr(self, key: str, default=None):
        if not isinstance(key, str):
            raise TypeError("Attribute key must be a string")

        return self.__attrs.get(key, default)

    # Method to remove an attribute
    def remove_attr(self, key: str):
        if not isinstance(key, str):
            raise TypeError("Attribute key must be a string")

        if key in self.__attrs:
            del self.__attrs[key]

    # Parent property
    @property
    def parent(self) -> 'Element':
        return self.__parent

    @parent.setter
    def parent(self, value: 'Element'):
        if value is not None and not isinstance(value, Element):
            raise TypeError("Parent must be an Element instance")
        self.__parent = value

    # Children property
    @property
    def childs(self) -> list['Element']:
        return self.__childs

    @childs.setter
    def childs(self, value: list['Element']):
        if not isinstance(value, list):
            raise TypeError("Children must be a list")

        # Validate all items are Element instances
        for child in value:
            if not isinstance(child, Element):
                raise TypeError("All children must be Element instances")

        self.__childs = value

    # Method to add a child
    def add_child(self, child: 'Element'):
        if not isinstance(child, Element):
            raise TypeError("Child must be an Element instance")

        self.__childs.append(child)
        child.parent = self

    # Method to remove a child
    def remove_child(self, child: 'Element'):
        if not isinstance(child, Element):
            raise TypeError("Child must be an Element instance")

        if child in self.__childs:
            self.__childs.remove(child)
            child.parent = None

    # Events property
    @property
    def events(self):
        return self.__events

    @events.setter
    def events(self, value: Events):
        if value and not isinstance(value, Events):
            raise TypeError('Events must be an Events instance')

        self.__events = value or Events()

    def add_event(self, event_type: EventType, event: callable):
        """Adds an event listener to the element."""
        if not isinstance(event_type, EventType):
            raise TypeError(f'event_type must be an EventType enum')

        if not callable(event):
            raise TypeError(f'event must be a callable function, but got {type(event)}')

        setattr(self.__events, event_type.value, event)

    def remove_event(self, event_type: EventType):
        """Removes an event listener from the element."""
        if not isinstance(event_type, EventType):
            raise TypeError(f'event_type must be an EventType enum')

        setattr(self.__events, event_type.value, None)

    def __repr__(self):
        return f"Element(name={self.name}, id={self.id}, uuid={self.uuid}, class_name={self.classes}, content={self.content}, attributes={self.attrs}, childs={len(self.childs)})"