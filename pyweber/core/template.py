import os
from uuid import uuid4
from pyweber.core.element import Element, SEARCH_MODE
from pyweber.utils.loads import LoadStaticFiles
from pyweber.config.config import config
from pyweber.utils.types import HTTPStatusCode, GetBy

class Template: # pragma: no cover
    def __init__(self, template: str, status_code: int = 200, title: str = None, include_uuid: bool = True, **kwargs):
        self.__include_uuid = include_uuid
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
        if not html: html = self.__template
        return self.__inject_default_elements(root=self.__parse_html(html=html))

    def build_html(self, include_doctype: bool = True):
        html = self.root.to_html()

        if include_doctype:
            html = f'<!DOCTYPE html>\n{html}'

        return html

    def getElement(
        self,
        by: GetBy,
        value: str,
        element: Element = None,
        search_mode: SEARCH_MODE='exact'
    ):
        if not element: element = self.root
        return element.getElement(by=by, value=value, search_mode=search_mode)

    def getElements(
        self,
        by: GetBy,
        value: str,
        element: Element = None,
        search_mode: SEARCH_MODE='exact'
    ):
        if not element: element = self.root
        return  element.getElements(by=by, value=value, search_mode=search_mode)

    def querySelector(
        self,
        selector: str,
        element: Element = None,
        search_mode: SEARCH_MODE='exact'
    ):
        if element is None: element = self.__root
        return element.querySelector(selector=selector, search_mode=search_mode)

    def querySelectorAll(
        self,
        selector: str,
        element: Element = None,
        search_mode: SEARCH_MODE='exact'
    ) -> list[Element]:
        if element is None: element = self.__root
        return element.querySelectorAll(selector=selector, search_mode=search_mode)

    def __parse_html(self, html: str) -> Element:
        if not html.replace('<!DOCTYPE html>', '').strip().startswith('<html'):
            if not html.startswith('<body'):
                html = f'<body>{html}</body>'
            html = f'<html>{html}</html>'

        element = Element.from_html(html=html, include_uuid=self.__include_uuid, **self.kwargs)

        if element.tag == 'html':
            if not element.querySelector('head'): element.childs.insert(0, Element('head'))

        return element

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
                root.childs[0].childs.extend(
                    [
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
