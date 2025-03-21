from pyweber.utils.types import getBy
from pyweber.core.base_element import ElementConstrutor
from pyweber.utils.types import HTMLTag, Events
from uuid import uuid4

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
        events = None
    ):
        super().__init__(tag, id, content, value, classes, style, attrs, childs, events)
        self.uuid = getattr(self, 'uuid', None) or str(uuid4())
    
    def getElement(self, by: getBy, value: str, element: 'Element' = None) -> 'Element':
        results = self.getElements(by=by, value=value, element=element)

        return results[0] if results else None
    
    def getElements(self, by: getBy, value: str, element: 'Element' = None) -> list['Element']:
        element = element or self
        results: list['Element'] = []

        if isinstance(by, getBy):
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
        
        elif getattr(element, by) == value:
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