import inspect
import json
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
from pyweber.models.routes import RouteManager
from pyweber.models.routes import Route


class Pyweber:
    def __init__(self, **kwargs):
        self.__update_handler: Callable = kwargs.get('update_handler', None)
        self.__middleware_manager = MiddlewareManager()
        self.__route_manager = RouteManager()
        self.__cookie_manager = CookieManager()
        self.error_pages = ErrorPages()
        self.__add_framework_routes()
        self.data = None
    
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

    def exists(self, route: str): return self.__route_manager.exists(route=route)
    def is_redirected(self, route: str): return self.__route_manager.is_redirected(route=route)
    def route_info(self, route: str, group: str): return self.__route_manager.route_info(route=route, group=group)
    def full_route(self, route: str, group: str): return self.__route_manager.full_route(route=route, group=group)

    def clear_routes(self): return self.__route_manager.clear_routes()
    def remove_route(self, route: str, group: str): return self.__route_manager.remove_route(route=route, group=group)
    def remove_redirected_route(self, route: str): return self.__route_manager.remove_redirected_route(route=route)

    def add_group_routes(self, routes: list[str], group: str = None): return self.__route_manager.add_group_routes(routes=routes, group=group)
    def remove_group(self, group: str): return self.__route_manager.remove_group(group=group)
    def get_group_routes(self, group: str = None): return self.__route_manager.get_group_routes(group=group)
    def get_group_by_route(self, route: str): return self.__route_manager.get_group_by_route(route=route)

    def get_route_by_path(self, route: str): return self.__route_manager.get_route_by_path(route=route)
    def get_route_by_name(self, name: str): return self.__route_manager.get_route_by_name(name=name)
    def get_redirected_route(self, route: str): return self.__route_manager.get_redirected_route(route=route)

    def resolve_path(self, route: str): return self.__route_manager.resolve_path(route=route)

    def route(self, route: str, methods: list[str] = None, group: str = None, name: str = None, middlewares: list[str] = None, status_code: int = None):
        return self.__route_manager.route(
            route=route,
            methods=methods,
            group=group,
            name=name,
            middlewares=middlewares,
            status_code=status_code
        )
    
    def add_route(
        self,
        route: str,
        template: Union[Callable, Template, Element, str, dict],
        methods: list[str] = None,
        group: str = None,
        name: str = None,
        middlewares: list[Callable] = None,
        status_code: int = None
    ):
        return self.__route_manager.add_route(
            route=route,
            template=template,
            methods=methods,
            group=group,
            name=name,
            middlewares=middlewares,
            status_code=status_code
        )
    
    def update_route(self, route: str, group: str=None, **kwargs):
        return self.__route_manager.update_route(route=route, group=group, **kwargs)
    
    def redirect(self, from_route: str, to_route: str, group: str):
        return self.__route_manager.redirect(from_route=from_route, to_route=to_route, group=group)
    
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
        
        if self.is_file_requested(route=request.path):
            status_code, content = self.get_static_files(route=request.path)

            return Response(
                request=request,
                code=status_code,
                response_content=content if isinstance(content, bytes) else str(content).encode(),
                response_type=self.get_content_type(route=request.path),
                route=request.path,
                cookies=self.cookies
            )
        
        status_code, template = await self.get_non_static_files(route=request.path, method=request.method)
        content_type, content = self.template_to_bytes(template=template)
        
        response = Response(
            request=request,
            response_content=content,
            code=status_code,
            cookies=self.cookies,
            response_type=content_type,
            route=request.path
        )
        
        # process after request middlewares
        after_request_response = await self.process_middleware(resp=response, middlewares=self.get_after_request_middleware)

        if after_request_response:
            _, response = after_request_response

            if not isinstance(response, Response):
                raise TypeError(f'All after request middleware need return Response instances, but got {type(response).__name__}')

        return response
    
    # Utils
    def template_to_bytes(self, template: Union[Template, Element, dict, str]) -> tuple[ContentTypes, bytes]:
        content_type = ContentTypes.html

        if isinstance(template, Template):
            template_str = template.build_html()
        elif isinstance(template, Element):
            template_str = template.to_html()
        elif isinstance(template, dict):
            template_str = json.dumps(template)
            content_type = ContentTypes.json
        else:
            template_str = Template(template=str(template)).build_html()
        
        return content_type, template_str.encode()
    
    def is_file_requested(self, route: str): return '.' in route.split('?')[0].split('/')[-1]

    def get_content_type(self, route: str) -> ContentTypes:
        if self.is_file_requested(route=route):
            extension = route.split('?')[0].split('/')[-1].split('.')[-1]
            for ext in ContentTypes.content_list():
                if extension == ext:
                    return getattr(ContentTypes, ext)
            return ContentTypes.unkown
        return ContentTypes.html
    
    def get_static_files(self, route: str):
        route, _ = self.resolve_path(route=route)
        try:
            if self.exists(route=route):
                content =  LoadStaticFiles(path=self.get_route_by_path(route=route).template).load
            else:
                content = LoadStaticFiles(path=route).load
            status_code =200

        except:
            content = b'File not found'
            status_code = 404
        
        return status_code, content

    async def get_non_static_files(self, route: str, method: str = 'GET'):
        path, kwargs = self.resolve_path(route=route)

        if self.is_redirected(route=path) or self.exists(route=path):
            if self.is_redirected(route=path):
                group, value = self.get_redirected_route(route=route).items()
                path = self.full_route(route=value, group=group)

            _route = self.get_route_by_path(route=path)

            if str(method).upper() in _route.methods:
                template = _route.template
                status_code = _route.status_code if not self.is_redirected(route=path) else 302

                if _route.middlewares:
                    route_middleware = await self.process_middleware(
                        resp=route,
                        middlewares=[
                            {
                                'status_code': None,
                                'middleware': middleware,
                                'order': None
                            } for middleware in _route.middlewares
                        ]
                    )

                    if route_middleware:
                        _, template = route_middleware
                try:
                    content = await self.process_templates(template=template, **kwargs)
                except Exception as error:
                    status_code = 500
                    content = Template(template=self.error_pages.page_server_error.build_html(), error=str(error))
                    PrintLine(error)
            else:
                status_code = 404
                content = self.error_pages.page_not_found

        else:
            status_code = 404
            content = self.error_pages.page_not_found
        
        return status_code, content
    
    async def process_templates(self, template: Union[Callable, Response, Template, Element, dict, str], **kwargs):
        if callable(template):
            if inspect.iscoroutinefunction(template):
                response: Template | Element | dict | str = await template(**kwargs)
            else:
                response: Template | Element | dict | str = template(**kwargs)
            
            template = response
        
        if isinstance(template, Element):
            response = Template(template=template.to_html())
        elif isinstance(template, str):
            response = Template(template=template)
        else:
            response = template

        return response
    
    def __add_framework_routes(self):
        self.add_group_routes(
            routes=[
                Route(
                    route='/admin',
                    template=str(StaticFilePath.admin_page.value)
                ),
                Route(
                    route='/_pyweber/admin/{uuid}/.css',
                    template=str(StaticFilePath.admin_css_file.value)
                ),
                Route(
                    route='/_pyweber/admin/{uuid}/.js',
                    template=str(StaticFilePath.admin_js_file.value)
                ),
                Route(
                    route='/_pyweber/static/favicon.ico',
                    template=str(StaticFilePath.favicon_path.value.joinpath('favicon.ico'))
                ),
                Route(
                    route='/_pyweber/static/{uuid}/.css',
                    template=str(StaticFilePath.pyweber_css.value)
                ),
                Route(
                    route='/_pyweber/static/{uuid}/.js',
                    template=str(StaticFilePath.js_base.value)
                )
            ]
        )
    
    async def clone_template(self, route: str):
        _, last_template = await self.get_non_static_files(route=route)
        
        return last_template.clone

    def update(self):
        return self.__update_handler() if self.__update_handler else None
    
    def launch_url(self, url: str, new_page: bool = False):
        return webbrowser.open(url=url, new=new_page)
    
    def to_url(self, url: str, new_page: bool = False):
        return window.open(url=url, new_page=new_page)
    
    def run(self, target: Callable = None, **kwargs):
        from pyweber.models.run import run
        return run(target, **kwargs)
    
    async def __call__(self, scope, receive, send):
        from pyweber.models.run import run_as_asgi
        await run_as_asgi(scope, receive, send, app=self)

    def __repr__(self):
        return f'Pyweber(routes={len(self.list_routes)})'