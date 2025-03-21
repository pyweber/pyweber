from pyweber.utils.types import Events, EventType, HTMLTag
from uuid import uuid4
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pyweber.core.template import Template

class ElementConstrutor:
    def __init__(
        self,
        tag: HTMLTag,
        id: str,
        content: str,
        value: str,
        classes: list[str],
        style: dict[str, str],
        attrs: dict[str, str],
        childs: list['ElementConstrutor'],
        events: Events,
    ):
        self.tag = tag
        self.id = id
        self.content = content
        self.value = value
        self.classes = classes or []
        self.style = style or {}
        self.attrs = attrs or {}
        self.childs = childs or []
        self.events = events or Events()
    
    @property
    def template(self):
        return self.__template
    
    @template.setter
    def template(self, value: 'Template'):
        self.__template = value
    
    @property
    def uuid(self):
        return self.__uuid
    
    @uuid.setter
    def uuid(self, value: str):
        if not value:
            self.__uuid = str(uuid4())
            return
        
        self.__uuid = value.strip()
    
    @property
    def tag(self):
        return self.__tag
    
    @tag.setter
    def tag(self, value: HTMLTag | str):
        if isinstance(value, HTMLTag):
            self.__tag = value.value
            return
        
        if not isinstance(value, str):
            raise TypeError('Element tag must be a HtmlTag ou string')
        
        if not value.strip():
            raise ValueError('Element tag name not be a dtring')
        
        self.__tag = value
    
    @property
    def id(self):
        return self.__id
    
    @id.setter
    def id(self, value: str):
        if not value:
            self.__id = None
            return

        if not isinstance(value, str):
            raise TypeError('Element id must be a string')
        
        self.__id = value.strip()
    
    @property
    def classes(self):
        return self.__classes
    
    @classes.setter
    def classes(self, class_name: list[str]):
        if class_name is None:
            self.__classes = []

        elif isinstance(class_name, list):
            if not all(isinstance(val, str) for val in class_name):
                raise TypeError('All element classes must to be a string')
        
        else:
            raise TypeError('Element classes must to be a string list')
        
        self.__classes = class_name
    
    def add_class(self, class_name: str):
        if not isinstance(class_name, str):
            raise TypeError('Class element must be a string')
        
        if class_name and not any(val not in self.__classes for val in class_name.split(' ')):
            self.__classes.extend(class_name.split(' '))
    
    def remove_class(self, class_name: str):
        if isinstance(class_name, str):
            for cls in class_name.split(' '):
                if cls in self.__classes:
                    self.__classes.remove(cls)
    
    def has_class(self, class_name: str):
        if isinstance(class_name, str):
            return all(cls in self.__classes for cls in class_name.split(' '))
        
        return False
    
    def toogle_class(self, class_name: str):
        if isinstance(class_name, str):
            for cls in class_name.split(' '):
                if cls in self.__classes:
                    self.__classes.remove(cls)
                else:
                    self.__classes.append(cls.strip())
    
    @property
    def style(self):
        return self.__style
    
    @style.setter
    def style(self, value: dict[str, str]):
        if not isinstance(value, dict):
            raise TypeError('Style value must be a dict of strings')
        
        if not all(isinstance(k, str) and isinstance(v, str) for k, v in value.items()):
            raise TypeError('All keys and values must be a string')
        
        self.__style = value
    
    def set_style(self, key: str, value: str):
        if not key or not value:
            raise ValueError('key and value cannot be empty or null')
        
        if not isinstance(key, str) or not isinstance(value, str):
            raise TypeError('Key or value must be a string')
        
        self.__style[key] = value
    
    def get_style(self, key: str):
        if key not in self.__style:
            raise KeyError('style not defined for this element')
        
        return self.__style.get(key, None)
    
    def remove_style(self, key: str):
        if key not in self.__style:
            raise TypeError('style not defined for this element')
        
        del self.__style[key]
    
    @property
    def attrs(self):
        return self.__attrs
    
    @attrs.setter
    def attrs(self, value: dict[str]):
        if not isinstance(value, dict):
            raise TypeError('attrs value must be a dict of strings')
        
        if not all(isinstance(k, str) and isinstance(v, str) for k, v in value.items()):
            raise TypeError('All keys and values must be a string')
        
        self.__attrs = value
    
    def set_attr(self, key: str, value: str):
        if not key or not value:
            raise ValueError('key and value cannot be empty or null')
        
        if not isinstance(key, str) or not isinstance(value, str):
            raise TypeError('Key or value must be a string')
        
        self.__attrs[key] = value
    
    def get_attr(self, key: str):
        if key not in self.__style:
            raise KeyError('style not defined for this element')
        
        return self.__attrs.get(key, None)
    
    def remove_attr(self, key: str):
        if key not in self.__style:
            raise TypeError('style not defined for this element')
        
        del self.__attrs[key]
    
    @property
    def content(self):
        return self.__content
    
    @content.setter
    def content(self, value: str):
        if value is None:
            self.__content = None
        else:
            try:
                self.__content = str(value)
            except Exception as e:
                raise ValueError(f"Could not convert value to string: {e}")
    
    @property
    def value(self):
        return self.__value
    
    @value.setter
    def value(self, value: str):
        if value is None:
            self.__value = value
        else:
            try:
                self.__value = str(value)
            except Exception as e:
                raise ValueError(f"Could not convert value to string: {e}")
    
    @property
    def parent(self):
        return self.__parent
    
    @parent.setter
    def parent(self, value: 'ElementConstrutor'):
        if value is None:
            self.__parent = None
            return
        
        if not isinstance(value, ElementConstrutor):
            raise TypeError("Parent must be an Element instance")

        self.__parent = value
    
    @property
    def childs(self):
        return self.__childs
    
    @childs.setter
    def childs(self, value: list['ElementConstrutor']):
        if not isinstance(value, list):
            raise TypeError("Children must be a list")
        
        if not all(isinstance(child, ElementConstrutor) for child in value):
            raise TypeError("All children must be Element instances")
        
        for child in value:
            child.parent = self
        
        self.__childs = value
    
    def add_child(self, child: 'ElementConstrutor'):
        if not isinstance(child,  ElementConstrutor):
            raise TypeError("Child must be Element instances")
        
        self.__childs.append(child)
        child.parent = self
    
    def remove_child(self, child: 'ElementConstrutor'):
        if child not in self.__childs:
            raise IndexError('Child not defined for this parent Element')
        
        self.__childs.remove(child)
        child.parent = None

    def pop_child(self, index: int = -1):
        if not isinstance(index, int):
            raise TypeError(f'Index must be a integer, but you got {type(index).__name__}')

        try:
            self.__childs.pop(index)
        
        except IndexError as e:
            raise IndexError(str(e))
    
    @property
    def events(self):
        return self.__events
    
    @events.setter
    def events(self, event_handler: Events):
        if not isinstance(event_handler, Events):
            raise TypeError('Event_handler must a be Events instance')
        
        self.__events = event_handler
    
    def add_event(self, event_type: EventType, event_handler: callable):
        if not isinstance(event_type, EventType):
            raise TypeError('Event_type must a be EventType instance')
        
        if not callable(event_handler):
            raise TypeError('Event_handler must a be callable function')
        
        setattr(self.__events, event_type, event_handler)
    
    def remove_event(self, event_type: EventType):
        if not isinstance(event_type, EventType):
            raise TypeError('Event_type must a be EventType instance')
        
        setattr(self.__events, event_type.value, None)