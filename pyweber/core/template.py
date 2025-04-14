import os
from typing import Callable
from uuid import uuid4
import lxml.html as HTMLPARSER
from lxml.etree import Element as LXML_Element
from pyweber.core.events import TemplateEvents
from pyweber.core.element import Element
from pyweber.utils.loads import LoadStaticFiles
from pyweber.config.config import config
from pyweber.utils.types import HTTPStatusCode, NonSelfClosingHTMLTags

class Template:
    def __init__(self, template: str, status_code: int = 200, **kwargs):
        self.__template = self.__read_file(file_path=template)
        self.kwargs = kwargs
        self.data = None
        self.__status_code = status_code
        self.__events: dict[str, Callable] = {}
        self.__icon: str = self.get_icon()
        self.__root = self.parse_html()
    
    @property
    def template(self):
        return self.__template
    
    @property
    def root(self):
        return self.__root
    
    @root.setter
    def root(self, value: Element):
        if value.tag != 'html':
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
        
        return self.__inject_default_elements(root=self.__parse_html(html=html))

    def build_html(self, element: Element = None, include_doctype: bool = True):
        element = element or self.__root
        html = self.__build_html(element=element)
        
        if include_doctype and element.tag == 'html':
            html = f'<!DOCTYPE html>\n{html}'
        
        return html
    
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
            return element.tag == selector
    
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
        
        if isinstance(HTMLElement, HTMLPARSER.HtmlComment):
            name = 'comment'
        else:
            name = HTMLElement.tag

        id = self.__render_dynamic_values(content=HTMLElement.attrib.pop('id', None))

        class_str = self.__render_dynamic_values(content=HTMLElement.attrib.pop('class', None))
        classes = class_str.split() if class_str else []

        style_str: str = self.__render_dynamic_values(content=HTMLElement.attrib.pop('style', None))
        style_dict = {}

        if style_str:
            style_pair = [s.strip() for s in style_str.split(';') if s.strip()]

            for pair in style_pair:
                if ':' in pair:
                    key, value = pair.split(':', 1)
                    style_dict[key.strip()] = value.strip()

        parent = parent
        uuid = HTMLElement.attrib.pop('uuid', None)
        value = self.__render_dynamic_values(content=HTMLElement.attrib.pop('value', None))
        content: str = self.__render_dynamic_values(content=HTMLElement.text if HTMLElement.text else None)
        events_dict = {key[1:]: HTMLElement.attrib.pop(key) for key in HTMLElement.attrib if key.startswith('_on')}
        childrens: list[HTMLPARSER.HtmlElement] = HTMLElement.getchildren()
        
        event_obj = TemplateEvents()
        for key, value in events_dict.items():
            if hasattr(event_obj, key):
                setattr(event_obj, key, value)

        element = Element(
            tag=name,
            id=id,
            classes=classes,
            value=value,
            content=content,
            events=event_obj,
            style=style_dict,
            attrs=dict(HTMLElement.attrib)
        )
        element.parent = parent
        element.template = self
        element.uuid = uuid

        if parent:
            if gettail(HTMLElement.tail):
                parent.content = parent.content or ''
                parent.content += f"{{{element.uuid}}} {gettail(HTMLElement.tail)}"

        for child in childrens:
            element.childs.append(self.__create_element(child, element))
        
        return element
    
    def __render_dynamic_values(self, content: str):
        if content:
            begin = content.find('{{')
            if begin != -1:
                end = content.find('}}')
                key = content[begin:end+2].removeprefix('{{').removesuffix('}}').strip()
                new_content = self.kwargs.get(key, None)
                
                if new_content:
                    if isinstance(new_content, Element):
                        new_content = self.build_html(element=new_content)
                    content = content.replace(content[begin:end+2], new_content)
        
        return content
    
    def __build_html(self, element: Element, indent: int = 0) -> str:
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
                if isinstance(value, str) or callable(value):
                    html += f" _{key}='{self.__event_id(value) if callable(value) else value}'"
                
                else:
                    raise ValueError(f'Event {value} is an invalid callable ou event_id')
            
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
            child_html = self.__build_html(child, indent + 4)
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

    def __read_file(self, file_path: str) -> str:
        if file_path.endswith('.html'):
            path = os.path.join('templates', file_path) if not os.path.isfile(file_path) else file_path
            
            if os.path.isfile(path=path):
                return LoadStaticFiles(path=path).load
            else:
                raise FileNotFoundError('The file not found, please include on templates file')
        
        return file_path
    
    def __create_default_element(self, *args, **kwargs):
        return Element(*args, **kwargs)
    
    def __inject_default_elements(self, root: Element):
        has_websocket_script, has_icon, has_description, has_css, has_keywords = False, False, False, False, False
        for child in root.childs[0].childs:
            if child.tag == 'script' and child.get_attr('src', '').startswith('/_pyweber/static/') and child.get_attr('src', '').endswith('/.js'):
                has_websocket_script = True
            
            elif child.tag == 'link':
                if 'icon' in list(child.attrs.values()):
                    has_icon = True
                
                elif child.get_attr('rel') == 'stylesheet' and child.get_attr('href', '').startswith('/_pyweber/static/') and child.get_attr('href', '').endswith('/.css'):
                    has_css = True
            
            elif child.tag == 'meta':
                if 'description' in list(child.attrs.values()):
                    has_description = True
                
                elif 'keywords' in list(child.attrs.values()):
                    has_keywords = True
            
            if has_websocket_script and has_icon and has_css and has_description and has_keywords:
                break
        
        if not has_websocket_script:
            root.childs[0].childs.extend(
                [
                    self.__create_default_element(
                        tag='script',
                        content=f"window.PYWEBER_WS_PORT = {os.environ.get('UVICORN_PORT', None) or os.environ.get('PYWEBER_WS_PORT', None) or config.get('websocket', 'port')}",
                        attrs={'type': 'text/javascript'}
                    ),
                    self.__create_default_element(
                        tag='script',
                        attrs={'src': f'/_pyweber/static/{str(uuid4())}/.js', 'type': 'text/javascript'}
                    )
                ]
            )
        
        if not has_icon:
            root.childs[0].childs.append(
                self.__create_default_element(
                    tag='link',
                    attrs={'rel': 'icon', 'href': f'{self.__icon.strip()}'.replace('\\', '/')}
                )
            )
        
        if not has_css:
            root.childs[0].childs.insert(
                1,
                self.__create_default_element(
                    tag='link',
                    attrs={'rel': 'stylesheet', 'href': f'/_pyweber/static/{str(uuid4())}/.css'}
                )
            )
        
        if not has_description:
            root.childs[0].childs.insert(
                0,
                self.__create_default_element(
                    tag='meta',
                    attrs={'name': 'description', 'content': config['app'].get('description')}
                )
            )
        
        if not has_keywords:
            root.childs[0].childs.insert(
                0,
                self.__create_default_element(
                    tag='meta',
                    attrs={'name': 'keywords', 'content': ', '.join(config['app'].get('keywords', []))}
                )
            )
        
        return root
    
    def __event_id(self, event: callable):
        key = f'event_{id(event)}'
        self.__events[key] = event
        return key