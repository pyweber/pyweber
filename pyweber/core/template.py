import os
import lxml.html as HTMLPARSER
from lxml.etree import Element as LXML_Element
from pyweber.core.elements import Element, Events
from pyweber.utils.load import LoadStaticFiles
from pyweber.config.config import config
from pyweber.utils.types import HTTPStatusCode

class Template:
    def __init__(self, template: str, status_code: int = 200):
        self.__template = self.__read_file(file_path=template)
        self.__events: dict[str, callable] = {}
        self.__icon: str = self.get_icon()
        self.__root = self.parse_html()
        self.__status_code = status_code
    
    @property
    def template(self):
        return self.__template
    
    @property
    def root(self):
        return self.__root
    
    @root.setter
    def root(self, value: Element):
        if value.name != 'html':
            raise ValueError('This Element is not valid to root. Please add the Html Element')
        
        self.__root = value
    
    @property
    def status_code(self):
        return self.__status_code
    
    @status_code.setter
    def status_code(self, code: int):
        if code not in HTTPStatusCode.code_list():
            raise ValueError(f'The code {code} is not a HttpStatusCode')
        
        self.__status_code = code

    @property
    def events(self):
        return self.__events

    def get_icon(self):
        return str(config['app'].get('icon'))
    
    def parse_html(self, html: str = None):
        if not html:
            html = self.__template
        
        root = self.__parse_html(html=html)

        has_websocket_script, has_icon = False, False
        for child in root.childs[0].childs:
            if child.name == 'script' and child.attrs.get('src', None) == '/_pyweber/static/js.js':
                has_websocket_script = True

            if child.name == 'link':
                if 'icon' in list(child.attrs.values()):
                    has_icon = True
            
            if has_icon and has_websocket_script:
                break
        
        if not has_websocket_script:
            root.childs[0].childs.extend(
                [
                    Element(
                        name='script',
                        content=f"window.PYWEBER_WS_PORT = {config['websocket'].get('port')}",
                        attrs={
                            'type': 'text/javascript'
                        }
                    ),
                    Element(
                        name='script',
                        attrs={
                            'src': '/_pyweber/static/js.js',
                            'type': 'text/javascript'
                        }
                    )
                ]
            )

        if not has_icon:
            root.childs[0].childs.append(
                Element(
                    name='link',
                    attrs={
                        'rel': 'icon',
                        'href': f'{self.__icon.strip()}'.replace('\\', '/'),
                    }
                )
            )
        
        return root

    def build_html(self, element: Element = None):
        if element:
            return f'<!DOCTYPE html>\n{self.__build_html(element=element)}'

        return f'<!DOCTYPE html>\n{self.__build_html(element=self.__root)}'
    
    def getElementById(self, element_id: str, element: Element = None) -> Element | None:
        if element is None:
            element = self.__root

        if element.id == element_id:
            return element

        for child in element.childs:
            result = self.getElementById(element_id, child)
            if result is not None:
                return result

        return None
    
    def getElementByUUID(self, element_uuid: str, element: Element = None) -> Element | None:
        if element is None:
            element = self.__root

        if element.uuid == element_uuid:
            return element

        for child in element.childs:
            result = self.getElementByUUID(element_uuid, child)
            if result is not None:
                return result

        return None

    def getElementByClass(self, class_name: str, element: Element = None) -> list[Element]:
        if element is None:
            element = self.__root

        results = []

        if element.classes and class_name in element.classes:
            results.append(element)

        for child in element.childs:
            results.extend(self.getElementByClass(class_name, child))

        return results
    
    def querySelector(self, selector: str, element: Element = None) -> Element | None:
        if element is None:
            element = self.__root

        if self.__matches_selector(element, selector):
            return element

        for child in element.childs:
            result = self.querySelector(selector, child)
            if result is not None:
                return result

        return None

    def querySelectorAll(self, selector: str, element: Element = None) -> list[Element]:
        if element is None:
            element = self.__root

        results = []

        if self.__matches_selector(element, selector):
            results.append(element)

        for child in element.childs:
            results.extend(self.querySelectorAll(selector, child))

        return results

    def __matches_selector(self, element: Element, selector: str) -> bool:
        if selector.startswith('#'):
            return element.id == selector[1:]
        elif selector.startswith('.'):
            return element.classes and selector[1:] in element.classes
        else:
            return element.name == selector
    
    def __parse_html(self, html: str) -> Element:
        if not html.replace('<!DOCTYPE html>', '').strip().startswith('<html'):
            if not html.startswith('<body'):
                html = f'<body>{html}</body>'
            html = f'<html>{html}</html>'
        
        root: HTMLPARSER.HtmlElement = HTMLPARSER.fromstring(html=html)
        
        if root.find(path='head') is None:
            root.insert(0, LXML_Element('head'))
        
        return self.__create_element(HTMLElement=root)
    
    def __create_element(self, HTMLElement: HTMLPARSER.HtmlElement, parent: Element = None):
        def gettail(html_element: str | None):
            try:
                return html_element.strip()
            except:
                return html_element
        
        name = HTMLElement.tag
        id = HTMLElement.attrib.pop('id', None)

        class_str = HTMLElement.attrib.pop('class', None)
        classes = class_str.split() if class_str else []

        style_str: str = HTMLElement.attrib.pop('style', None)
        style_dict = {}

        if style_str:
            style_pair = [s.strip() for s in style_str.split(';') if s.strip()]

            for pair in style_pair:
                if ':' in pair:
                    key, value = pair.split(':', 1)
                    style_dict[key.strip()] = value.strip()

        parent = parent
        value = HTMLElement.attrib.pop('value', None)
        uuid = HTMLElement.attrib.pop('uuid', None)
        content = HTMLElement.text.strip() if HTMLElement.text else None
        events_dict = {key[1:]: HTMLElement.attrib.pop(key) for key in HTMLElement.attrib if key.startswith('_on')}
        childrens: list[HTMLPARSER.HtmlElement] = HTMLElement.getchildren()
        
        event_obj = Events()
        for key, value in events_dict.items():
            if hasattr(event_obj, key):
                setattr(event_obj, key, value)

        element = Element(
            name=name,
            id=id,
            classes=classes,
            parent=parent,
            value=value,
            content=content,
            events=event_obj,
            uuid=uuid,
            style=style_dict,
            attrs=dict(HTMLElement.attrib),
            template=self
        )

        if parent:
            if gettail(HTMLElement.tail):
                parent.content = parent.content if parent.content else ''
                parent.content += f" «{element.uuid}»{gettail(HTMLElement.tail)}"

        for child in childrens:
            element.childs.append(self.__create_element(child, element))
        
        return element
    
    def __build_html(self, element: Element, indent: int = 0) -> str:
        indentation = ' ' * indent
        html = f'{indentation}<{element.name} uuid="{element.uuid}"'

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
            html += f' {key}{f'="{value}"' if value else ''}'

        for key, value in element.events.__dict__.items():
            if value is not None:
                if isinstance(value, str) or callable(value):
                    html += f' {f"_{key}"}="{self.__event_id(value) if callable(value) else value}"'
                
                else:
                    raise ValueError(f'Event {value} is an invalid callable ou event_id')
            
        if not element.content and not element.childs and element.name != 'script':
            return html + '>'
        
        html += '>'
        
        final_content = str((element.content or '')).strip()
        has_children = bool(element.childs)
        
        if has_children or '\n' in final_content:
            html += '\n'
        
        for child in element.childs:
            child_html = self.__build_html(child, indent + 4)
            uuid_placeholder = f' «{child.uuid}»'
            
            if uuid_placeholder in final_content:
                final_content = final_content.replace(uuid_placeholder, child_html.strip())
            else:
                final_content += '\n' + child_html
        
        if final_content:
            if has_children or '\n' in final_content:
                html += ' ' * (indent + 4) + final_content.strip() + '\n' + indentation
            else:
                html += final_content.strip()
        
        html += f'</{element.name}>'
        
        return html

    def __read_file(self, file_path: str) -> str:
        if file_path.endswith('.html'):
            path = os.path.join('templates', file_path)
            if os.path.isfile(path=path):
                return LoadStaticFiles(path=path).load
            else:
                raise FileNotFoundError('The file not found, please include on templates file')
        
        return file_path
    
    def __event_id(self, event: object):
        key = f'event_{id(event)}'
        self.__events[key] = event

        return key