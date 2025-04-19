from pyweber.core.template import Template
from pyweber.core.element import Element
from typing import Literal

class TemplateDiff:
    def __init__(self, new_element: Element, old_element: Element):
        self.new_element = new_element
        self.old_element = old_element
        self.differences: dict[str, dict[str, str]] = {}
        self.checked_elements: list[Element] = []
        self.track_differences()
    
    def track_differences(self, new_element: Element = None, old_element: Element = None):
        if not new_element:
            new_element = self.new_element
        
        if not old_element:
            old_element = self.old_element
        
        status = None
        
        if new_element.uuid != old_element.uuid:
            status = 'Added'

        else:
            if new_element.id != old_element.id:
                status = 'Changed'
            
            elif new_element.content != old_element.content:
                status = 'Changed'
            
            elif new_element.value != old_element.value:
                status = 'Changed'
            
            elif new_element.tag != old_element.tag:
                status = 'Changed'
            
            elif new_element.attrs != old_element.attrs:
                status = 'Changed'
            
            elif new_element.style != old_element.style:
                status = 'Changed'
            
            elif new_element.events.__dict__ != old_element.events.__dict__:
                status = 'Changed'
            
            elif [v for v in new_element.classes if v not in old_element.classes]:
                status = 'Changed'
        
        if status:
            self.add_element_on_diff(element=new_element, status=status)

            if status == 'Added':
                self.add_element_on_diff(element=old_element, status='Removed')

            self.checked_elements.append(new_element.uuid)
        
        new_element_childs_map = {child.uuid: child for child in new_element.childs}
        old_element_childs_map = {child.uuid: child for child in old_element.childs}
        
        for uuid, old_child in old_element_childs_map.items():
            if uuid in new_element_childs_map:
                if old_child.parent and old_child.parent.uuid not in self.checked_elements:
                    self.track_differences(new_element_childs_map[uuid], old_child)
            
            else:
                self.add_element_on_diff(element=old_child, status='Removed')

        for uuid, new_child in new_element_childs_map.items():
            if uuid not in old_element_childs_map:
                self.add_element_on_diff(element=new_child, status='Added')
    
    def add_element_on_diff(self, element: Element, status: Literal['Added', 'Changed', 'Removed']):
        self.differences[str(len(self.differences))] = {
            'parent': element.parent.uuid if element.parent else None,
            'element': element.to_html() if status in ['Added', 'Changed'] else element.uuid,
            'status': status
        }