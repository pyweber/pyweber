from uuid import uuid4
from typing import TYPE_CHECKING, Callable, Union
from pyweber.core.events import TemplateEvents
from pyweber.utils.types import EventType, HTMLTag, NonSelfClosingHTMLTags

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
        events: 'TemplateEvents',
        **kwargs
    ):
        self.kwargs = kwargs
        self.tag = tag
        self.id = id
        self.content = content
        self.value = value
        self.classes = classes or []
        self.style = style or {}
        self.attrs = attrs or {}
        self.childs = childs or []
        self.events = events or TemplateEvents()
        self.parent = None
        self.data = None
    
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
            raise TypeError('Element tag must be an HtmlTag ou string')
        
        if not value.strip():
            raise ValueError('Element tag name not be an empty value')
        
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
        
        if class_name and any(val not in self.__classes for val in class_name.split(' ')):
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
    
    def get_style(self, key: str, default= None):
        return self.__style.get(key, default)
    
    def remove_style(self, key: str):
        if key in self.__style:
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
    
    def get_attr(self, key: str, default=None) -> str | None:        
        return self.__attrs.get(key, default)
    
    def remove_attr(self, key: str):
        if key in self.__attrs:
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
    def events(self):
        return self.__events
    
    @events.setter
    def events(self, event_handler: 'TemplateEvents'):
        if not isinstance(event_handler, TemplateEvents):
            raise TypeError('Event_handler must a be Events instance')
        
        self.__events = event_handler
    
    def add_event(self, event_type: EventType, event_handler: callable):
        if not isinstance(event_type, EventType):
            raise TypeError('Event_type must a be EventType instance')
        
        if not callable(event_handler):
            raise TypeError('Event_handler must a be callable function')
        
        setattr(self.__events, event_type.value, event_handler)
    
    def remove_event(self, event_type: EventType):
        if not isinstance(event_type, EventType):
            raise TypeError('Event_type must a be EventType instance')
        
        setattr(self.__events, event_type.value, None)
    
    def to_html(self, element: 'ElementConstrutor' = None, indent: int = 0):
        if not element:
            element = self
        
        if not isinstance(element, ElementConstrutor):
            raise TypeError(f'element must be an Element instances, but got {type(element).__name__}')
        
        indentation = ' ' * indent
        html = f"{indentation}<{element.tag} uuid='{element.uuid}'" if element.tag != 'comment' else f'{indentation}<!--'

        if element.id:
            html += f' id="{element.id}"'
        if element.classes and len(element.classes) > 0:
            html += f' class="{" ".join(element.classes)}"'
        if element.value:
            html += f' value="{element.value}"'

        if element.style and len(element.style) > 0:
            style_str = '; '.join([f"{key}: {value}" for key, value in element.style.items()])
            html += f' style="{style_str}"'
            
        for key, value in element.attrs.items():
            if value:
                html += f" {key}='{value}'"
            else:
                html += f" {key}"

        for key, value in element.events.__dict__.items():
            if value is not None:
                html += f" _{key}='{self.create_event_id(value)}'"
            
        if not element.content and not element.childs and element.tag not in NonSelfClosingHTMLTags.non_autoclosing_tags():
            if element.tag == 'comment':
                return html + '-->'
            else:
                return html + '>'
        
        if element.tag != 'comment':
            html += '>'
        
        final_content = str((self.__render_dynamic_values(content=element.content) or ''))
        has_children = bool(element.childs)
        
        if has_children or '\n' in final_content:
            html += '\n'
        
        for child in element.childs:
            child_html = self.to_html(child, indent + 4)
            uuid_placeholder = f'{{{child.uuid}}}'
            
            if uuid_placeholder in final_content:
                final_content = final_content.replace(uuid_placeholder, child_html)
            else:
                final_content += '\n' + child_html
        
        if final_content:
            if has_children or '\n' in final_content:
                html += ' ' * (indent + 4) + final_content.strip() + '\n' + indentation
            else:
                html += final_content.strip()
        
        html += f'</{element.tag}>' if element.tag != 'comment' else '-->'

        return html
    
    def __render_dynamic_values(self, content: str):
        if content:
            begin = content.find('{{')
            if begin != -1:
                end = content.find('}}')
                key = content[begin:end+2].removeprefix('{{').removesuffix('}}').strip()
                new_content = self.kwargs.get(key, None)
                
                if new_content:
                    if isinstance(new_content, ElementConstrutor):
                        new_content = self.to_html(element=new_content)
                    content = content.replace(content[begin:end+2], new_content)
        
        return content

    def create_event_id(self, event: Union[Callable, str]):
        if isinstance(event, str) or callable(event):
            from pyweber.core.events import EventBook

            if isinstance(event, str):
                event_id = EventBook.get(event, None)

                if not event_id:
                    raise KeyError(f'{event} not in Pyweber EventBook.')
                
                return event

            elif callable(event):
                event_id = f'event_{id(event)}'
                EventBook[event_id] = event
            
                return event_id

        raise ValueError(f'Event {event.__name__} is an invalid callable ou event_id')
    
    def __repr__(self):
        return (
            f'Element('
            f'tag={self.tag}, '
            f'id={self.id}, '
            f'classes={self.classes}, '
            f'content_length={len(str(self.content)) if self.content else 0}, '
            f'value={self.value}, '
            f'parent={bool(self.parent)}, '
            f'childs={len(self.childs)})'
        )