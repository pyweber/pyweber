import inspect
import json
import os
import re
import webbrowser
import traceback
import logging
from typing import Union, Callable, Any
from dataclasses import dataclass
from pyweber.core.element import Element
from pyweber.core.template import Template
from pyweber.models.request import Request
from pyweber.models.response import Response
from pyweber.utils.types import ContentTypes, StaticFilePath, HTTPStatusCode
from pyweber.utils.loads import LoadStaticFiles
from pyweber.core.window import window
from pyweber.connection.websocket import WebsocketManager

from pyweber.models.middleware import MiddlewareManager
from pyweber.models.error_pages import ErrorPages
from pyweber.models.cookies import CookieManager
from pyweber.models.routes import (
    Route,
    RedirectRoute,
    RouteManager,
)

from pyweber.models.openapi import OpenApiProcessor

from pyweber.utils.utils import PrintLine
    

@dataclass
class StateResult: # pragma: no cover
    template: Any
    status_code: int
    content_type: ContentTypes
    redirect_path: str
    process_response: bool
    kwargs: dict[str, Any]
    callback: Callable[..., Any]

    def update(
        self,
        template = None,
        status_code = None,
        content_type = None,
        redirect_path = None,
        process_response = None,
        callback = None,
        kwargs = {}
    ):
        self.template = template if template else self.template
        self.status_code = status_code if status_code else self.status_code
        self.content_type = content_type if content_type else self.content_type
        self.redirect_path = redirect_path if redirect_path else self.redirect_path
        self.process_response = process_response if process_response is not None else self.process_response
        self.callback = callback if callback is not None else self.callback
        self.kwargs = kwargs if kwargs else self.kwargs

        return self

@dataclass
class TemplateResult: # pragma: no cover
    status_code: int
    content_type: ContentTypes
    redirect_path: str
    process_response: bool
    template: Union[Template, Element, dict, list, str]

@dataclass
class ContentResult: # pragma: no cover
    content: bytes
    content_type: ContentTypes

    def __post__init__(self):
        if not isinstance(self.content_type, ContentTypes):
            raise TypeError(f"content_type must be ContentTypes, got {type(self.content_type).__name__}")
        
        if not isinstance(self.content, bytes):
            raise TypeError(f"content must be bytes, got {type(self.content).__name__}")

class Pyweber(
    ErrorPages,
    CookieManager,
    MiddlewareManager,
    RouteManager
): # pragma: no cover
    def __init__(self, **kwargs):
        MiddlewareManager.__init__(self)
        RouteManager.__init__(self)
        CookieManager.__init__(self)
        ErrorPages.__init__(self)
        self.__update_handler: Callable = kwargs.get('update_handler', None)
        self.__add_framework_routes()
        self.data = None
        self.__visited__ = set()
        self.__request: Request = None
        self.__cache_templates: dict[str, tuple[ContentResult, TemplateResult]] = {}
    
    # Request
    @property
    def request(self): return self.__request

    # Project Run
    @property
    def run(self):
        from pyweber.models.run import run
        return run
    
    def clear_cache_templates(self):
        self.__cache_templates.clear()
    
    @property
    def ws_server(self): return self.__ws_server

    @ws_server.setter
    def ws_server(self, value: WebsocketManager):
        assert isinstance(value, WebsocketManager)
        self.__ws_server = value

    # Response
    async def get_response(self, request: Request) -> Response:
        if not isinstance(request, Request):
            raise TypeError(f'request must be a Request instances, but got {type(request).__name__}')
        
        if re.search(r'^/_pyweber/(?:.*?)/openapi.json$', request.path):
            await self.__add_openapi_route()
        
        _route, _ = self.resolve_path(route=request.path)
        title = None
        _route_method = f"{_route}_{request.method}"

        if _route_method in self.__cache_templates:
            content_result, template_result = self.__cache_templates[_route_method]

        else:
            if _route in self.list_routes:
                title = self.get_route_by_path(route=_route).title
                self.__request = request
            
            # process before request middlewares
            before_request_response = await self.process_middleware(
                resp=request,
                middlewares=self.get_before_request_middlewares
            )
            
            if before_request_response:
                template_result = await self._process_templates(
                    state_result=StateResult(
                        template=before_request_response.content,
                        status_code=before_request_response.status_code,
                        process_response=before_request_response.process_response,
                        content_type=ContentTypes.html,
                        redirect_path=request.path,
                        callback=None,
                        kwargs={}
                    )
                )
            
            else:
                template_result = await self.get_template(
                    route=request.path,
                    method=request.method
                )

            content_result = self.template_to_bytes(
                template=template_result.template,
                content_type=template_result.content_type,
                title=title,
                process_response=template_result.process_response
            )

            # self.__cache_templates[_route_method] = (content_result, template_result)
        
        # process after request middlewares
        after_request_response = await self.process_middleware(
            resp=Response(
                request=request,
                response_content=content_result.content,
                response_type=content_result.content_type,
                code=template_result.status_code,
                cookies=self.cookies,
                route=template_result.redirect_path
            ),
            middlewares=self.get_after_request_middlewares
        )

        # To prevent Recursion Error
        if template_result.redirect_path in self.__visited__:
            self.__visited__.remove(template_result.redirect_path)

        return after_request_response.content
    
    # Utils
    def template_to_bytes(
        self,
        template: Union[Template, Element, dict, list, set, str, bytes],
        content_type: ContentTypes = ContentTypes.html,
        title: str = None,
        process_response: bool = False
    ):
        if isinstance(template, Template):
            return self._process_template_object(template=template, title=title, content_type=content_type)
        
        elif isinstance(template, Element):
            return self._process_element_object(
                element=template,
                title=title,
                content_type=content_type,
                process_template=process_response
            )
        
        elif isinstance(template, (dict, set, list)):
            return self._process_json_object(template=template)

        elif isinstance(template, bytes):
            return self._process_byte_object(data=template, content_type=content_type)
        
        else:
            return self._process_string_object(
                data=template,
                title=title,
                content_type=content_type,
                process_response=process_response
            )
    
    def _process_byte_object(self, data: bytes, content_type: ContentTypes):
        return ContentResult(content=data, content_type=content_type)
    
    def _process_json_object(self, template: Union[dict, list, set]):
        return ContentResult(content=json.dumps(template).encode(), content_type=ContentTypes.json)
    
    def _process_template_object(self, template: Template, title: str, content_type: ContentTypes):
        template.title = title if title else template.title
        return ContentResult(content=template.build_html().encode(), content_type=content_type)
    
    def _process_element_object(
        self,
        element: Element,
        title: str,
        content_type: ContentTypes,
        process_template: bool
    ):        
        if process_template:
            return ContentResult(
                content=Template(template=element.to_html(), title=title).build_html().encode(),
                content_type=content_type
            )
        
        return ContentResult(content=element.to_html().encode(), content_type=content_type)
    
    def _process_string_object(
        self,
        data: str,
        title: str,
        content_type: ContentTypes,
        process_response: bool
    ):
        if not isinstance(data, str):
            data = str(data)
        
        if process_response and content_type == ContentTypes.html:
            return ContentResult(
                content=Template(template=data, title=title).build_html().encode(),
                content_type=content_type
            )
        
        return ContentResult(content=data.encode(), content_type=content_type)

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

        state_result = StateResult(
            template=None,
            status_code=404,
            content_type=ContentTypes.html,
            process_response=True,
            kwargs=kwargs,
            callback=None,
            redirect_path=path
        )

        if self.exists(route=path):
            _route = self.get_route_by_path(route=path)

            if method in _route.methods:
                if self.is_redirected(route=path):
                    redirect_route = self.get_redirected_route(route=path)
                    kwargs = redirect_route.kwargs or redirect_route.route.kwargs

                    state_result.update(
                        kwargs=kwargs,
                        status_code=redirect_route.status_code,
                        redirect_path=self.build_route(_route.full_route, **kwargs),
                        template=_route.template,
                        process_response=_route.process_response,
                        content_type=_route.content_type,
                        callback=_route.callback
                    )
                else:
                    state_result.update(
                        template=_route.template,
                        process_response=_route.process_response,
                        status_code=_route.status_code,
                        content_type=_route.content_type,
                        callback=_route.callback,
                        kwargs=kwargs
                    )
                
                if _route.middlewares:
                    middleware_result = await self.process_route_middleware(
                        resp=self.request,
                        middlewares=_route.middlewares,
                        status_code=_route.status_code
                    )

                    if middleware_result:
                        state_result.update(
                            template=middleware_result.content,
                            status_code=middleware_result.status_code,
                            process_response=middleware_result.process_response
                        )
    
        if not state_result.template or isinstance(state_result.template, str):
            path = state_result.template or path

            if self.is_static_file(route=path) or self.is_file_requested(route=path):
                content_type = self.get_content_type(route=self.normaize_path(route=path))
                if self.is_static_file(route=path):
                    state_result.update(
                        template=self.load_static_files(path=path),
                        content_type=content_type,
                        status_code=200
                    )
                else:
                    state_result.update(
                        template=b'File not found',
                        status_code=404,
                        content_type=content_type
                    )
            else:
                content_type = self.get_content_type(route=path)

                state_result.update(
                    template=self.page_not_found,
                    content_type=self.get_content_type(route=route),
                    process_response=False if content_type.value != ContentTypes.html.value else True
                )
        
        return await self._process_templates(state_result=state_result)   

    def _check_recursion(self, route: str):
        if route in self.__visited__:
            raise RecursionError(f'Recursion detected for route {route}')
        self.__visited__.add(route)
    
    async def _process_redirect_route(
        self,
        state: StateResult,
        redirect_route: RedirectRoute,
        redirect_path: str,
        **kwargs
    ):
        if redirect_route.route.middlewares:
            middleware_result = await self.process_route_middleware(
                resp=self.request,
                middlewares=redirect_route.route.middlewares,
                status_code=redirect_route.status_code
            )

            if middleware_result:
                return state.update(
                    status_code=middleware_result.status_code,
                    process_response=middleware_result.process_response,
                    template=middleware_result.content
                )
        
        return state.update(
            template=redirect_route.route.template,
            status_code=redirect_route.status_code,
            content_type=redirect_route.route.content_type,
            redirect_path=redirect_path,
            process_response=redirect_route.route.process_response,
            callback=redirect_route.route.callback,
            kwargs=redirect_route.kwargs or kwargs
        )

    async def _process_templates(self, state_result: StateResult):
        try:
            template = state_result.template

            while callable(template) or isinstance(template, RedirectRoute):
                if callable(template):
                    request_body = self.request.body if self.request else {}
                    kwargs = OpenApiProcessor.prepare_callback_kwargs(
                        callback=state_result.callback,
                        **{**state_result.kwargs, **request_body}
                    )

                    template = await template(**kwargs) if inspect.iscoroutinefunction(template) else template(**kwargs)
                
                if isinstance(template, RedirectRoute):
                    redirect_path = self.build_route(route=template.route.full_route, **state_result.kwargs)

                    self._check_recursion(route=redirect_path)
                    state_result = await self._process_redirect_route(
                        state=state_result,
                        redirect_route=template,
                        redirect_path=redirect_path,
                        **state_result.kwargs
                    )

                    template = state_result.template
        
        except Exception as error:
            error_details = {
                'type': type(error).__name__,
                'message': str(error),
                'traceback': traceback.format_exc(),
                'line': traceback.extract_tb(error.__traceback__)[-1].lineno
            }

            logging.error(traceback.format_exc())
            
            template = Template(
                template=self.page_server_error.build_html(),
                error=f'{error_details["message"]}, line {error_details["line"]}'
            )
            state_result.status_code = HTTPStatusCode.INTERNAL_SERVER_ERROR.code
            state_result.content_type = ContentTypes.html
            
        return TemplateResult(
            status_code=state_result.status_code,
            content_type=state_result.content_type,
            redirect_path=state_result.redirect_path,
            process_response=state_result.process_response,
            template=template
        )
    
    async def process_route_middleware(self, resp: str, middlewares: list[Callable], status_code: int):
        return await self.process_middleware(
            resp=resp,
            middlewares=[
                {
                    'status_code': status_code,
                    'middleware': middleware,
                    'process_middleware': False,
                    'order': None
                } for middleware in middlewares
            ]
        )
    
    def is_file_requested(self, route: str):
        return re.match(r".*(\.[a-zA-Z0-9]+)+$", route.split('?')[0].split('/')[-1]) is not None
    
    def is_static_file(self, route: str):
        return os.path.isfile(path=route) or os.path.isfile(self.normaize_path(route=route))
    
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
                    route='/docs',
                    template=StaticFilePath.pyweber_docs.value,
                    title='Pyweber Documentation'
                ),
                Route(
                    route='/_pyweber/admin/{uuid}/.css',
                    template=StaticFilePath.admin_css_file.value,
                    content_type=ContentTypes.css
                ),
                Route(
                    route='/_pyweber/admin/{uuid}/.js',
                    template=StaticFilePath.admin_js_file.value,
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
    
    async def __add_openapi_route(self):
        route = '/_pyweber/{uuid}/openapi.json'

        if route not in self._RouteManager__routes:
            self.add_group_routes([
                Route(
                    route=route,
                    template=self.__get_routes(),
                    content_type=ContentTypes.json
                )
            ])
    
    def __get_routes(self):
        list_routes = [self.get_route_by_path(route) for route in self.list_routes if route not in ['/docs']]
        schema = {
            "openapi": "3.0.0",
            "info": {
                "title": "Pyweber Documentation",
                "version": "1.0.0"
            },
            "paths": {}
        }

        for route in list_routes:
            if isinstance(route, Route):
                schema['paths'][route.route] = {}

                for method in route.methods:
                    schema['paths'][route.route][method.lower()] = {
                        "summary": route.title or 'Pyweber Route',
                        "parameters": [
                            v for _, v in OpenApiProcessor.get_route_spec(route.route, route.callback).items()
                        ],
                        "responses": {
                            str(route.status_code): {
                                "description": HTTPStatusCode.search_name_by_code(route.status_code)
                            },
                            str(500): {
                                'description': HTTPStatusCode.search_name_by_code(500)
                            }
                        }
                    }

                    request_body = OpenApiProcessor.get_body_spec(route.route, route.callback)

                    if request_body.get('content') and route.callback.__name__ != '<lambda>':
                        schema['paths'][route.route][method.lower()]['requestBody'] = request_body

        return schema
    
    async def clone_template(self, route: str):
        template_result = await self.get_template(route=route)

        if not isinstance(template_result.template, Template):
            template_result.template = Template(template=str(template_result.template))
        
        return template_result.template.clone()

    def update(self, changed_file: str = None):
        return self.__update_handler(module=changed_file) if self.__update_handler else None
    
    def launch_url(self, url: str, new_page: bool = False):
        return webbrowser.open(url=url, new=new_page)
    
    def to_url(self, url: str, new_page: bool = False, message: str = None):
        window.open(url=url, new_page=new_page)
        return Element(
            tag='p',
            content=message or f"Redirected to {Element( tag='a', attrs={'href': url}, content=url).to_html()}"
        )
    
    async def __call__(self, scope, receive, send):
        from pyweber.models.run import run_as_asgi

        await run_as_asgi(scope, receive, send, app=self)

    def __repr__(self):
        return f'Pyweber(routes={len(self.list_routes)})'