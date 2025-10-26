from uuid import uuid4
from typing import Union, Any
from pyweber.utils.types import HTMLTag, GetBy
from pyweber.models.file import File
from pyweber.models.element import (
    ElementConstrutor,
    TemplateEvents,
    ChildElements
)

class Element(ElementConstrutor): # pragma: no cover
    def __init__(
        self,
        tag: HTMLTag,
        childs: ChildElements = None,
        id: str = None,
        content: Any = None,
        value: Any = None,
        classes: list[str] = None,
        style: dict[str, str] = None,
        attrs: dict[str, str] = None,
        events: TemplateEvents = None,
        data: Any = None,
        sanitize: bool = False,
        files: list[File] = None,
        **kwargs: str
    ):
        super().__init__(
            tag=tag,
            childs=childs,
            id=id,
            content=content,
            value=value,
            classes=classes,
            style=style,
            attrs=attrs,
            events=events,
            sanitize=sanitize,
            files=files,
            **kwargs
        )
        self.uuid = getattr(self, 'uuid', None) or str(uuid4())
        self.data = data
    
    @property
    def parent(self):
        return self.__parent
    
    @parent.setter
    def parent(self, value: 'Element'):
        if value is None:
            self.__parent = None
            return
        
        if not isinstance(value, Element):
            raise TypeError("Parent must be an Element instance")

        self.__parent = value
    
    @property
    def childs(self):
        return self.__childs
    
    @childs.setter
    def childs(self, value: ChildElements):
        if not isinstance(value, (list, ChildElements)):
            raise TypeError(f"Children must be a ChildElements instances, but got {type(value).__name__}")
        
        if isinstance(value, list):
            value = ChildElements(self).extend(value)

        value = self.__render_dynamic_elements(childs=value)
        
        self.__childs = value
    
    def add_child(self, child: 'Element'):
        if not isinstance(child,  Element):
            raise TypeError("Child must be Element instances")
        
        self.__childs.append(child)
        child.parent = self
    
    def remove_child(self, child: 'Element'):
        if child not in self.__childs:
            raise IndexError('Child not defined for this parent Element')
        
        self.__childs.remove(child)
        child.parent = None

    def pop_child(self, index: int = -1):
        if not isinstance(index, int):
            raise TypeError(f'Index must be a integer, but you got {type(index).__name__}')

        return self.__childs.pop(index)
    
    def getElement(self, by: GetBy, value: str, element: 'Element' = None) -> 'Element':
        results = self.getElements(by=by, value=value, element=element)

        return results[0] if results else None
    
    def getElements(self, by: GetBy, value: str, element: 'Element' = None) -> list['Element']:
        element = element or self
        results: list['Element'] = []

        if isinstance(by, GetBy):
            by: str = by.value
        
        if by == 'classes':
            if set(value.split()) <= set(element.classes):
                results.append(element)
        
        elif by in ['attrs', 'style']:
            conditions: list[str] = [pair.strip() for pair in value.split(';') if pair.strip()]
            has = False

            el: dict[str, str] = getattr(element, by, {})
            for condition in conditions:
                key, _, val = condition.partition(':')

                if not val: key, _, val = condition.partition('=')

                if not val:
                    if key.strip() in el:
                        has = True

                elif key.strip() in el and el.get(key.strip(), None) == val.strip():
                    has = True
            
            if has:
                results.append(element)
        
        elif getattr(element, by, None) == value:
            results.append(element)
        
        if element.childs:
            for child in element.childs:
                results.extend(self.getElements(by=by, value=value, element=child))
        
        return results
    
    def querySelector(self, selector: str, element: 'Element' = None) -> 'Element':
        results = self.querySelectorAll(selector=selector, element=element)

        return results[0] if results else None
    
    def querySelectorAll(self, selector: str, element: 'Element' = None) -> list['Element']:
        element = element or self
        results: list['Element'] = []

        if selector.startswith('.'):
            classes = ' '.join(selector.split('.')).strip()
            return self.getElements(by=GetBy.classes, value=classes)
        
        elif selector.startswith('#'):
            if selector[1:].strip() == element.id:
                results.append(element)
        
        elif selector.startswith('['):
            sel = selector.removeprefix('[').removesuffix(']')
            return self.getElements(by=GetBy.attrs, value=sel)
        
        else:
            if selector.strip() == element.tag:
                results.append(element)
        
        for child in element.childs:
            results.extend(self.querySelectorAll(selector=selector, element=child))

        return results
    
    def __render_dynamic_elements(self, childs: ChildElements):
        new_childs: ChildElements = ChildElements(self)
        if childs:
            for child in childs:
                if isinstance(child, str):
                    if not child.startswith('{{') or not child.endswith('}}'):
                        raise ValueError("{} must be starts with '{{' and ends with '}}'".format(child))
                    
                    key = child.removeprefix('{{').removesuffix('}}').strip()
                    element = self.kwargs.get(key, None)

                    if not element:
                        self.content = (self.content or '') + child

                    elif isinstance(element, ElementConstrutor):
                        new_childs.append(element)
                
                elif isinstance(child, ElementConstrutor):
                    new_childs.append(child)
                
                else:
                    raise TypeError(f'all childs must be str or Element instances, but got {type(child).__name__}')
        
        return new_childs

    @property
    def clone(self):
        from pyweber.core.events import TemplateEvents
        
        element = self

        cln = Element(
            tag=element.tag,
            id=element.id,
            content=element.content,
            value=element.value,
            classes=self.__deepy_clone(element.classes),
            style=self.__deepy_clone(element.style),
            attrs=self.__deepy_clone(element.attrs),
            events=TemplateEvents(**element.events.__dict__),
            **element.kwargs
        )
        cln.uuid = element.uuid
        cln.parent = element.parent
        cln.template = getattr(element, 'template', None)

        for child in element.childs:
            cln.childs.append(child.clone)

        return cln
    
    def __deepy_clone(self, obj):
        if isinstance(obj, list):
            return [self.__deepy_clone(item) for item in obj]
        elif isinstance(obj, dict):
            return {chave: self.__deepy_clone(valor) for chave, valor in obj.items()}
        else:
            return obj