from uuid import uuid4
from typing import Union
from pyweber.utils.types import HTMLTag, GetBy
from pyweber.models.element import ElementConstrutor

class Element(ElementConstrutor):
    def __init__(
        self,
        tag,
        id = None,
        content = None,
        value = None,
        classes = None,
        style = None,
        attrs = None,
        childs: list['Element'] = None,
        events = None,
        **kwargs
    ):
        super().__init__(tag, id, content, value, classes, style, attrs, childs, events, **kwargs)
        self.uuid = getattr(self, 'uuid', None) or str(uuid4())
    
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
    def childs(self, value: list['Element']):
        if not isinstance(value, list):
            raise TypeError("Children must be a list")
        
        value = self.__render_dynamic_elements(childs=value)
        
        for child in value:
            child.parent = self
        
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

        try:
            self.__childs.pop(index)
        
        except IndexError as e:
            raise IndexError(str(e))
    
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
            has = True

            el: dict[str, str] = getattr(element, by, {})
            for condition in conditions:
                key, _, value = condition.partition(':')

                if key.strip() not in el or el.get(key.strip(), None) != value.strip():
                    has = False
            
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
            if set(selector[1:].strip()) <= set(element.classes):
                results.append(element)
        
        elif selector.startswith('#'):
            if selector[1:].strip() == element.id:
                results.append(element)
        
        elif selector.startswith('['):
            sel = selector.removeprefix('[').removesuffix(']')

            attr, value = sel.split('=')

            if attr.strip() in HTMLTag:
                results.extend(self.getElements(by=attr.strip(), value=value.strip(), element=element))
        
        else:
            if selector.strip() == element.tag:
                results.append(element)
        
        for child in element.childs:
            results.extend(self.querySelectorAll(selector=selector, element=child))

        return list(dict.fromkeys(results))
    
    def __render_dynamic_elements(self, childs: list[Union['ElementConstrutor', str]]):
        new_childs: list['ElementConstrutor'] = []
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