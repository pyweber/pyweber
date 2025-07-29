import os
from uuid import uuid4
import lxml.html as HTMLPARSER
from lxml.etree import Element as LXML_Element
from pyweber.core.events import TemplateEvents
from pyweber.core.element import Element
from pyweber.utils.loads import LoadStaticFiles
from pyweber.config.config import config
from pyweber.utils.types import HTTPStatusCode

class Template: # pragma: no cover
    def __init__(self, template: str, status_code: int = 200, title: str = None, **kwargs):
        self.__template = self.__read_file(file_path=template)
        self.kwargs = kwargs
        self.data = None
        self.__status_code = status_code
        self.__icon: str = self.get_icon()
        self.title = title
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
        from pyweber.core.events import EventBook
        return EventBook
    
    @property
    def title(self): return self.__title

    @title.setter
    def title(self, value: str):
        self.__title = value

        if hasattr(self, 'root'):
            title = self.root.getElement(by='tag', value='title')

            if title:
                title.content = value if value else title.content
    
    @property
    def head(self): return self.root.querySelector('head')
    
    @property
    def body(self): return self.root.querySelector('body')

    @property
    def style(self): return self.root.querySelectorAll('style')[-1]

    def get_icon(self):
        return str(config['app'].get('icon'))
    
    def parse_html(self, html: str = None):
        if not html:
            html = self.__template
        
        return self.__inject_default_elements(root=self.__parse_html(html=html))

    def build_html(self, include_doctype: bool = True):
        html = self.root.to_html()
        
        if include_doctype:
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
        for key, event in events_dict.items():
            if hasattr(event_obj, key):
                setattr(event_obj, key, event)

        element = Element(
            tag=name,
            id=id,
            classes=classes,
            value=value,
            content=content,
            events=event_obj,
            style=style_dict,
            attrs=dict(HTMLElement.attrib),
            **self.kwargs
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
                    content = content.replace(content[begin:end+2], str(new_content))
        
        return content

    def __read_file(self, file_path: str) -> str:
        from pyweber.models.error_pages import ErrorPages
        if file_path.endswith('.html'):
            path = os.path.join('templates', file_path) if not os.path.isfile(file_path) else file_path
            
            try:
                return LoadStaticFiles(path=path).load
            
            except FileNotFoundError:
                return ErrorPages().page_server_error.build_html().replace(
                    "{{error}}",
                    f'{path} not found, please include on templates file'
                )
        
        return file_path
    
    def __create_default_element(self, *args, **kwargs):
        return Element(*args, **kwargs)
    
    def __inject_default_elements(self, root: Element):
        has_websocket_script, has_icon, has_description, has_css, has_keywords, has_title = False, False, False, False, False, False
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
            
            elif child.tag == 'title':
                has_title = child
            
            if has_websocket_script and has_icon and has_css and has_description and has_keywords and has_title:
                break
        
        if not has_websocket_script:
            # insert websockets port if exists
            disable_ws = os.environ.get('PYWEBER_DISABLE_WS', False)

            if disable_ws not in [True, 'True', 'true', '1', 1]:
                ws_port = os.environ.get('UVICORN_PORT', None) or os.environ.get('PYWEBER_WS_PORT', None) or config.get('websocket', 'port')
                root.childs[0].childs.extend(
                    [
                        self.__create_default_element(
                            tag='script',
                            content=f"window.PYWEBER_WS_PORT = {ws_port}",
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
        
        if isinstance(has_title, Element):
            has_title.content = self.title if self.title else has_title.content
            
        else:
            root.childs[0].childs.append(
                self.__create_default_element(
                    tag='title',
                    content=self.title if self.title else config.get('app', 'name')
                )
            )

        return root
    
    def clone(self):
        tpl = Template(
            template=self.template,
            status_code=self.status_code,
            title=self.title,
            **self.kwargs
        )
        tpl.data = self.data
        tpl.root = self.root.clone

        return tpl