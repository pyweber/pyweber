import inspect
import json
import os
import re
import webbrowser
from datetime import datetime
from typing import Union, Callable, Literal
from pyweber.core.element import Element
from pyweber.core.template import Template
from pyweber.models.request import Request
from pyweber.models.response import Response
from pyweber.utils.types import ContentTypes, StaticFilePath
from pyweber.utils.loads import LoadStaticFiles
from pyweber.utils.utils import PrintLine
from pyweber.core.window import window

from pyweber.models.middleware import MiddlewareManager
from pyweber.models.error_pages import ErrorPages
from pyweber.models.cookies import CookieManager
from pyweber.models.routes import (
    Route,
    RedirectRoute,
    RouteManager
)


class Pyweber:
    def __init__(self, **kwargs):
        self.__update_handler: Callable = kwargs.get('update_handler', None)
        self.__middleware_manager = MiddlewareManager()
        self.__route_manager = RouteManager()
        self.__cookie_manager = CookieManager()
        self.error_pages = ErrorPages()
        self.__add_framework_routes()
        self.data = None
        self.__visited__ = set()
    
    # Error pages

    @property
    def error_pages(self):
        return self.__error_pages
    
    @error_pages.setter
    def error_pages(self, error_pages: ErrorPages):
        if not isinstance(error_pages, ErrorPages):
            raise TypeError(f'Error Page must be an Error Pages instances, but got {type(error_pages).__name__}')
        
        self.__error_pages = error_pages
    
    # Cokkie Manager
    @property
    def cookies(self): return self.__cookie_manager.cookies

    def set_cookie(
        self,
        cookie_name: str,
        cookie_value: str,
        path: str = '/',
        samesite: Literal['Strict', 'Lax', None] = 'Strict',
        httponly: bool = True,
        secure: bool= True,
        expires: datetime = None
    ):
        return self.__cookie_manager.set_cookie(
            cookie_name=cookie_name,
            cookie_value=cookie_value,
            path=path,
            samesite=samesite,
            httponly=httponly,
            secure=secure,
            expires=expires
        )
    
    # Middlewares

    @property
    def get_before_request_middleware(self):
        return self.__middleware_manager.get_before_request_middlewares
    
    @property
    def get_after_request_middleware(self):
        return self.__middleware_manager.get_after_request_middlewares
    
    def before_request(self, status_code: int = 200, order: int=-1):
        return self.__middleware_manager.before_request(status_code=status_code, order=order)
    
    def after_request(self, status_code: int = None, order: int=-1):
        return self.__middleware_manager.after_request(status_code=status_code, order=order)
    
    def clear_before_request_middleware(self):
        return self.__middleware_manager.clear_before_request_middleware()
    
    def clear_after_request_middleware(self):
        return self.__middleware_manager.clear_after_request_middleware()
    
    async def process_middleware(self, resp: Request | Response, middlewares: list[dict[str, int | Callable]]):
        return await self.__middleware_manager.process_middleware(resp=resp, middlewares=middlewares)

    # Router
    
    @property
    def list_routes(self): return self.__route_manager.list_routes
    @property
    def list_redirected_routes(self): return self.__route_manager.list_redirected_routes

    def exists(self, route: str): return self.__route_manager.exists(route=route)
    def is_redirected(self, route: str): return self.__route_manager.is_redirected(route=route)
    def route_info(self, target: str): return self.__route_manager.route_info(target=target)
    def full_route(self, route: str, group: str=None): return self.__route_manager.full_route(route=route, group=group)

    def clear_routes(self): return self.__route_manager.clear_routes()
    def remove_route(self, route: str, group: str=None): return self.__route_manager.remove_route(route=route, group=group)
    def remove_redirected_route(self, route: str): return self.__route_manager.remove_redirected_route(route=route)

    def add_group_routes(self, routes: list[str], group: str = None): return self.__route_manager.add_group_routes(routes=routes, group=group)
    def remove_group(self, group: str): return self.__route_manager.remove_group(group=group)
    def get_group_routes(self, group: str = None): return self.__route_manager.get_group_routes(group=group)
    def get_group_by_route(self, route: str): return self.__route_manager.get_group_by_route(route=route)

    def get_route_by_path(self, route: str, follow_redirect: bool = True): return self.__route_manager.get_route_by_path(route=route, follow_redirect=follow_redirect)
    def get_route_by_name(self, name: str): return self.__route_manager.get_route_by_name(name=name)
    def get_redirected_route(self, route: str): return self.__route_manager.get_redirected_route(route=route)

    def resolve_path(self, route: str): return self.__route_manager.resolve_path(route=route)
    def build_route(self, route: str, **kwargs): return self.__route_manager.build_route(route=route, **kwargs)

    def route(
        self,
        route: str,
        methods: list[str] = None,
        group: str = None,
        name: str = None,
        middlewares: list[str] = None,
        status_code: int = None,
        content_type: ContentTypes = None
    ):
        return self.__route_manager.route(
            route=route,
            methods=methods,
            group=group,
            name=name,
            middlewares=middlewares,
            status_code=status_code,
            content_type=content_type
        )
    
    def add_route(
        self,
        route: str,
        template: Union[Callable, Template, Element, str, dict],
        methods: list[str] = None,
        group: str = None,
        name: str = None,
        middlewares: list[Callable] = None,
        status_code: int = None,
        content_type: ContentTypes = None
    ):
        return self.__route_manager.add_route(
            route=route,
            template=template,
            methods=methods,
            group=group,
            name=name,
            middlewares=middlewares,
            status_code=status_code,
            content_type=content_type
        )
    
    def update_route(self, route: str, group: str=None, **kwargs):
        return self.__route_manager.update_route(route=route, group=group, **kwargs)
    
    def redirect(self, from_route: str, target: str, status_code: int = 302, **kwargs):
        return self.__route_manager.redirect(from_route=from_route, target=target, status_code=status_code, **kwargs)
    
    def to_route(self, target: str, status_code=302, **kwargs):
        return self.__route_manager.to_route(target=target, status_code=status_code, **kwargs)
    
    def inspect_function(self, callback: Callable):
        return self.__route_manager.inspect_function(callback=callback)

    # Response
    async def get_response(self, request: Request):
        if not isinstance(request, Request):
            raise TypeError(f'request must be a Request instances, but got {type(request).__name__}')
        
        # process before request middlewares
        before_request_response = await self.process_middleware(resp=request, middlewares=self.get_before_request_middleware)

        if before_request_response:
            status_code, response = before_request_response
            content_type, content = self.template_to_bytes(template=response)
            return Response(
                request=request,
                response_content=content,
                code=status_code,
                cookies=self.cookies,
                response_type=content_type,
                route=request.path
            )
        
        status_code, content_type, redirect_path, template = await self.get_template(
            route=request.path,
            method=request.method
        )

        content_type, content = self.template_to_bytes(template=template, content_type=content_type)
        
        response = Response(
            request=request,
            response_content=content,
            code=status_code,
            cookies=self.cookies,
            response_type=content_type,
            route=redirect_path
        )
        
        # process after request middlewares
        after_request_response = await self.process_middleware(resp=response, middlewares=self.get_after_request_middleware)

        if after_request_response:
            _, response = after_request_response

            if not isinstance(response, Response):
                raise TypeError(f'All after request middleware need return Response instances, but got {type(response).__name__}')

        return response
    
    # Utils
    def template_to_bytes(self, template: Union[Template, Element, dict, str, bytes], content_type: ContentTypes = ContentTypes.html) -> tuple[ContentTypes, bytes]:
        template_str = None
        template_bytes = b''

        if not isinstance(content_type, ContentTypes):
            PrintLine(template)
            raise TypeError(f'content_type does not NoneType')

        if isinstance(template, Template):
            template_str = template.build_html()
        elif isinstance(template, Element):
            template_str = template.to_html()
        elif isinstance(template, dict):
            template_str = json.dumps(template)
            content_type = ContentTypes.json
        elif isinstance(template, bytes):
            template_bytes = template
            content_type = content_type or ContentTypes.unkown
        elif isinstance(template, str):
            if content_type.value in ['text/html', 'text/plain']:
                template_str = Template(template=template).build_html()
                content_type = ContentTypes.html
            else:
                template_str = template
        else:
            template_str = Template(template=str(template)).build_html()
        
        template_bytes = template_str.encode() if isinstance(template_str, str) else template_bytes
        
        return content_type, template_bytes

    def get_content_type(self, route: str) -> ContentTypes:
        if self.is_file_requested(route=route):
            extension = route.split('?')[0].split('/')[-1].split('.')[-1]
            for ext in ContentTypes.content_list():
                if extension == ext:
                    return getattr(ContentTypes, ext)
            return ContentTypes.unkown
        return ContentTypes.html

    async def get_template(self, route: str, method: str = 'GET'):
        path, kwargs = self.resolve_path(route=route)
        status_code, content_type, redirect_path, template = 404, ContentTypes.html, route, path
        if self.exists(route=path):
            status_code, _kwargs = 200, {}

            if self.is_redirected(route=path):
                redirected_route = self.get_redirected_route(route=path)
                _kwargs = redirected_route.kwargs
                status_code = redirected_route.status_code
                _route = redirected_route.route
                kwargs = redirected_route.kwargs or kwargs
                redirect_path = self.build_route(_route.full_route, **kwargs)
            else:
                _route = self.get_route_by_path(route=route, follow_redirect=False)
            
            if str(method).upper() in _route.methods:
                template = _route.template
                
                kwargs = _kwargs or kwargs
                status_code = status_code or _route.status_code
                content_type = _route.content_type

                if _route.middlewares:
                    self.__visited__.add(route)
                    _status_code, _template = await self.process_route_middleware(
                        resp=route,
                        middlewares=_route.middlewares,
                        status_code=status_code
                    )

                    if _template:
                        return await self.final_response(
                            template=_template,
                            status_code=_status_code,
                            redirect_path=redirect_path,
                            content_type=content_type,
                            **kwargs
                        )
                
        if template == path:
            if self.is_static_file(route=path):
                status_code, content_type, template = 200, self.get_content_type(route=path), self.load_static_files(path=path)
            else:
                status_code, content_type, template =  404, ContentTypes.html, self.error_pages.page_not_found

        return await self.final_response(
            template=template,
            status_code=status_code,
            redirect_path=redirect_path,
            content_type=content_type,
            **kwargs
        )

    async def final_response(self, template, status_code, content_type, redirect_path, **kwargs):
        _status_code, _content_type, _redirect_path, template = await self.process_templates(template=template, **kwargs)

        status_code = _status_code or status_code
        redirect_path = _redirect_path or redirect_path
        content_type = _content_type or content_type

        if isinstance(template, str) and (self.is_static_file(route=template) or self.is_file_requested(route=template)):
            content_type = self.get_content_type(route=self.normaize_path(route=template))
            if self.is_static_file(route=template):
                status_code = 200 if status_code == 404 else status_code
                template = self.load_static_files(path=template)

            else:
                status_code, template = status_code, b'Not found'
        
        if isinstance(template, str):
            if content_type.value in ['text/html', 'text/plain']:
                template = Template(template=template)
                content_type = ContentTypes.html

        return status_code, content_type, redirect_path, template     

    async def process_templates(self, template: Union[Callable, Template, Element, dict, str], **kwargs):
        status_code: int = None
        content_type: ContentTypes = None
        redirect_path = None

        while callable(template) or isinstance(template, RedirectRoute):
            if callable(template):
                template = await template(**kwargs) if inspect.iscoroutinefunction(template) else template(**kwargs)
            
            if isinstance(template, RedirectRoute):
                builded_route = self.build_route(route=template.route.full_route, **kwargs)

                if builded_route in self.__visited__:
                    raise RecursionError(f'Recursion detected for route {builded_route}')
                self.__visited__.add(builded_route)

                kwargs = template.kwargs or kwargs
                status_code = status_code or template.status_code
                content_type = template.route.content_type
                redirect_path = builded_route
                kwargs = template.kwargs or kwargs

                if template.route.middlewares:
                    status_code, template = await self.process_route_middleware(
                        resp=builded_route,
                        middlewares=template.route.middlewares,
                        status_code=status_code
                    )

                    if not callable(template) or not isinstance(template, RedirectRoute):
                        return await self.final_response(
                            template=template,
                            status_code=status_code,
                            content_type=content_type,
                            redirect_path=redirect_path,
                            **kwargs
                        )
                
                template = template.route.template

        if isinstance(template, Element):
            response = Template(template=template.to_html())
        
        else:
            response = template
        
        return status_code, content_type, redirect_path, response
    
    async def process_route_middleware(self, resp: str, middlewares: list[Callable], status_code: int):
        status_code, response = status_code, None
        if isinstance(middlewares, list):
            midd_resp = await self.process_middleware(
                resp=resp,
                middlewares=[{
                    'status_code': status_code,
                    'middleware': middleware,
                    'order': None
                } for middleware in middlewares]
            )

            if midd_resp:
                status_code, response = midd_resp[0], midd_resp[-1]
        
        return status_code, response
    
    def is_file_requested(self, route: str):
        return re.match(r".*(\.[a-zA-Z0-9]+)+$", route.split('?')[0].split('/')[-1]) is not None
    
    def is_static_file(self, route: str):
        return os.path.isfile(self.normaize_path(route=route))
    
    def normaize_path(self, route: str):
        return os.path.normpath(path=route.removeprefix('/'))
    
    def load_static_files(self, path: os.path):
        return LoadStaticFiles(path=path).load

    def __add_framework_routes(self):
        self.add_group_routes(
            routes=[
                Route(
                    route='/admin',
                    template=str(StaticFilePath.admin_page.value)
                ),
                Route(
                    route='/_pyweber/admin/{uuid}/.css',
                    template=str(StaticFilePath.admin_css_file.value),
                    content_type=ContentTypes.css
                ),
                Route(
                    route='/_pyweber/admin/{uuid}/.js',
                    template=str(StaticFilePath.admin_js_file.value),
                    content_type=ContentTypes.js
                ),
                Route(
                    route='/_pyweber/static/favicon.ico',
                    template=str(StaticFilePath.favicon_path.value.joinpath('favicon.ico')),
                    content_type=ContentTypes.ico
                ),
                Route(
                    route='/_pyweber/static/{uuid}/.css',
                    template=str(StaticFilePath.pyweber_css.value),
                    content_type=ContentTypes.css
                ),
                Route(
                    route='/_pyweber/static/{uuid}/.js',
                    template=str(StaticFilePath.js_base.value),
                    content_type=ContentTypes.js
                )
            ]
        )
    
    async def clone_template(self, route: str):
        _, _, _, last_template = await self.get_template(route=route)
        
        return last_template.clone

    def update(self):
        return self.__update_handler() if self.__update_handler else None
    
    def launch_url(self, url: str, new_page: bool = False):
        return webbrowser.open(url=url, new=new_page)
    
    def to_url(self, url: str, new_page: bool = False, message: str = None):
        window.open(url=url, new_page=new_page)
        return Element(
            tag='p',
            content=message or f"Redirected to {Element(
                tag='a',
                attrs={'href': url},
                content=url
            ).to_html()}"
        )
    
    def run(self, target: Callable = None, **kwargs):
        from pyweber.models.run import run
        return run(target, **kwargs)
    
    async def __call__(self, scope, receive, send):
        from pyweber.models.run import run_as_asgi
        await run_as_asgi(scope, receive, send, app=self)

    def __repr__(self):
        return f'Pyweber(routes={len(self.list_routes)})'