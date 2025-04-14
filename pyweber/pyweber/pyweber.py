import requests
import inspect
import json
import asyncio
import webbrowser
import sys
import traceback
from datetime import datetime
from typing import Union, Callable, Any
from pyweber.core.template import Template
from pyweber.models.request import Request
from pyweber.models.response import Response
from pyweber.utils.types import ContentTypes, StaticFilePath
from pyweber.utils.loads import StaticTemplates, LoadStaticFiles
from pyweber.utils.utils import PrintLine
from pyweber.utils.exceptions import (
    InvalidRouteFormatError,
    InvalidTemplateError,
    RouteAlreadyExistError,
    RouteNotFoundError
)

class Pyweber:
    def __init__(self, **kwargs):
        self.__routes: dict[str, Union[Template, Callable[..., Union[Template, str, dict]]]] = {}
        self.__redirects: dict[str, str] = {}
        self.__update_handler = kwargs.get('update_handler', None)
        self.__before_request: list[dict[str, Union[int, Callable[..., Any]]]] = []
        self.__after_request: list[dict[str, Union[int, Callable[..., Any]]]] = []
        self.__cookies: list[str] = []
        self.__serve_static_framework_files
        self.page_unauthorized = Template(template=StaticTemplates.PAGE_UNAUTHORIZED(), status_code=401)
        self.page_not_found = Template(template=StaticTemplates.PAGE_NOT_FOUND(), status_code=404)
        self.page_server_error = Template(template=StaticTemplates.PAGE_SERVER_ERROR(), status_code=500)
        self.data = None
    
    @property
    def list_routes(self) -> list[str]:
        return [key for key in self.__routes if '_pyweber' not in key]
    
    @property
    def _list_framework_routes_(self) -> list[str]:
        return [key for key in self.__routes if '_pyweber' in key]
    
    @property
    def clear_routes(self) -> None:
        self.__routes.clear()
    
    @property
    def page_not_found(self):
        return self.__page_not_found
    
    @property
    def page_unauthorized(self):
        return self.__page_unauthorized
    
    @property
    def page_server_error(self):
        return self.__page_server_error
    
    @page_unauthorized.setter
    def page_unauthorized(self, template: Template = None):
        if not isinstance(template, Template):
            raise InvalidTemplateError()

        self.__page_unauthorized = template
    
    @page_not_found.setter
    def page_not_found(self, template: Template = None):
        if not isinstance(template, Template):
            raise InvalidTemplateError()

        self.__page_not_found = template
    
    @page_server_error.setter
    def page_server_error(self, template: Template):
        if not isinstance(template, Template):
            raise InvalidTemplateError()
        
        self.__page_server_error = template
    
    @property
    def cookies(self):
        return self.__cookies
    
    @property
    def clear_before_request(self):
        self.__before_request.clear()
        
    
    def before_request(self, status_code: int = 200):
        def wrapper(middle_func: callable):
            self.__before_request.append({'status_code': status_code, 'middle_func': middle_func})
            return middle_func
        return wrapper

    @property
    def clear_after_request(self):
        self.__after_request.clear()
    
    def after_request(self):
        def wrapper(middle_func: callable):
            self.__after_request.append({'status_code': None, 'middle_func': middle_func})
            return middle_func
        return wrapper

    def route(self, route: str):
        def decorator(template_func: Callable[..., Union[Template, dict, str]]):
            async def wrapper(**kwargs):
                if inspect.iscoroutinefunction(template_func):
                    self.update_route(route=route, template= await template_func(**kwargs))
                else:
                    self.update_route(route=route, template=template_func(**kwargs))
                return self.__routes[route]
            self.add_route(route=route, template=wrapper)
            return wrapper
        return decorator
    
    def add_route(self, route: str, template: Union[Template, Callable[..., Union[Template, dict, str]], dict, str]) -> None:

        if not route.startswith('/'):
            raise InvalidRouteFormatError()
        
        elif route in self.__routes:
            raise RouteAlreadyExistError(route=route)
        
        elif callable(template) or isinstance(template, Template):
            self.__routes[route] = template

        elif isinstance(template, dict):
            self.__routes[route] = json.dumps(template, ensure_ascii=False)

        else:
            self.__routes[route] = Template(template=str(template))
    
    def update_route(self, route: str, template: Union[Template, Callable]) -> None:
        if route not in self.__routes:
            raise RouteNotFoundError(route=route)
        
        elif callable(template) or isinstance(template, Template):
            self.__routes[route] = template

        elif isinstance(template, dict):
            self.__routes[route] = template

        else:
            self.__routes[route] = Template(template=str(template))

    def remove_route(self, route: str) -> None:
        if route not in self.__routes:
            raise RouteNotFoundError(route=route)
        del self.__routes[route]

    def redirect(self, from_route: str, to_route: str) -> None:
        if to_route not in self.__routes:
            raise RouteNotFoundError(route=to_route)
        self.__redirects[from_route] = to_route
    
    async def get_route(self, request: Request):

        # middleware before_request
        __response: tuple[int, Union[dict, Template, Any]] | None = await self.__process_middleware(resp=request, middle_list=self.__before_request)

        if __response:
            status_code, response = __response
            if isinstance(response, dict):
                response_content = json.dumps(response, ensure_ascii=False)
                content_type = ContentTypes.json

            elif isinstance(response, Template):
                status_code = status_code or response.status_code
                response_content = response.build_html()
                content_type = self.get_content_type(route=request.path)
            
            else:
                template = Template(template=str(response))
                status_code = status_code or template.status_code
                response_content = template.build_html()
                content_type = self.get_content_type(route=request.path)
            
            return Response(
                request=request,
                response_content=response_content.encode(),
                code=status_code,
                cookies=self.cookies,
                response_type=content_type,
                route=request.path
            )
        
        elif request.netloc:
            response = requests.request(method='GET', url=request.get_url)
            content = response.content
            content_type = self.get_content_type(route=request.path)
            code = response.status_code
            route = request.path
        
        else:
            __resp = await self.get_template(route=request.path)

            content = __resp.content
            content_type = __resp.content_type
            code = __resp.status_code
            route=__resp.route
        
        if isinstance(content, Template):
            content = content.build_html().encode()
        
        elif isinstance(content, str):
            content = content.encode()

        response = Response(
            request=request,
            response_content=content,
            code=code,
            response_type=content_type,
            route=route,
            cookies=self.cookies
        )
        
        # middleware after request
        __response = await self.__process_middleware(resp=response, middle_list=self.__after_request)

        if __response:
            _, response = __response
            if not isinstance(response, Response):
                raise TypeError('You middled function must be return a valid Response instance.')
            return response
        
        return response

    def get_redirected_route(self, route: str) -> str:
        return self.__redirects[route]
    
    
    async def async_get_content(self, callback: Callable, **kwargs) -> Union[Template, dict, str]:
        if inspect.iscoroutinefunction(callback):
            try:
                loop = asyncio.get_running_loop()
                return await callback(**kwargs)
            
            except RuntimeError:
                return asyncio.run(callback(**kwargs))
        else:
            return callback(**kwargs)
    
    async def __get_content_requested(self, path: str):
        """Get content to non static file (existing route)
        - `path` (str): real_path accoring with route requested with client
        """
        if self.is_redirected(route=path):
            content = self.__routes[self.__redirects[path]]
            route=self.get_redirected_route(path)
        else:
            content = self.__routes[path]
            route = path
        
        return route, content
    
    async def __get_response_content(self, content: Union[Template, dict, str], **kwargs):
        if callable(content):
            try:
                resp_content = await self.async_get_content(content, **kwargs)
            except Exception as error:
                PrintLine(text=f'{self.__error_traceback()}')
                resp_content = self.page_server_error
                error_element = resp_content.querySelector('.error-content')

                if error_element:
                    error_element.content = str(error)

            return resp_content
        
        return content
    
    async def __get_response_to_file_request(self, path: str, route: str):
        """Get response to static file
        - `path` (str): real_path accoring with route requested with client
        - `route` (str): route requested with client
        """
        try:
            if path in self.__routes:
                content = LoadStaticFiles(self.__routes.get(path)).load
            else:
                content = LoadStaticFiles(route).load
            status_code = 200
        
        except FileNotFoundError:
            content = b'File not found'
            status_code = 404
        
        return ResponseStruct(
            content=content if isinstance(content, bytes) else content,
            status_code=status_code,
            content_type=self.get_content_type(route=route),
            route=route
        )
    
    async def __get_response_to_non_file_request(self, path: str, **kwargs):
        if path in self.__routes or self.is_redirected(route=path):
            route, content = await self.__get_content_requested(path=path)
            response_content = await self.__get_response_content(content=content, **kwargs)

            if isinstance(response_content, Template):
                content_type = ContentTypes.html
                status_code = (
                    302 if self.is_redirected(path)
                    and not str(response_content.status_code).startswith('3')
                    else response_content.status_code
                )

            elif isinstance(response_content, dict):
                response_content = json.dumps(response_content, ensure_ascii=False)
                content_type = ContentTypes.json
                status_code = 200

            else:
                response_content = Template(template=str(response_content))
                content_type = ContentTypes.html
                status_code = response_content.status_code

        else:
            response_content = self.page_not_found
            status_code = response_content.status_code
            content_type = ContentTypes.html
            route = path
        
        return ResponseStruct(
            content=response_content,
            status_code=status_code,
            content_type=content_type,
            route=route
        )

    async def get_template(self, route: str):
        path, kwargs = self.__resolve_path(route=route)

        if self.is_file_request(route=route):
            return await self.__get_response_to_file_request(path=path, route=route)
        
        return await self.__get_response_to_non_file_request(path=path, **kwargs)
    
    async def clone_template(self, route: str) -> Template:
        last_template = await self.get_template(route=route)
        last_template = last_template.content
        new_template = Template(last_template.template, status_code=last_template.status_code)
        new_template.root = last_template.root
        new_template._Template__events = last_template.events
        new_template._Template__icon = last_template.get_icon()
        new_template.data = last_template.data
        return new_template
    
    def get_content_type(self, route: str) -> ContentTypes:
        l_text = route.split('/')[-1]

        if '.' in l_text:
            extension = l_text.split('.')[-1].strip()

            for ext in ContentTypes:
                if extension == ext.name:
                    return ext
        
            return ContentTypes.unkown
        
        return ContentTypes.html
    
    def is_file_request(self, route: str) -> bool:
        return '.' in route.strip().split('/')[-1]
    
    def exists(self, route: str) -> bool:
        return route in self.__routes
    
    def is_redirected(self, route: str) -> bool:
        return route in self.__redirects
    
    def __resolve_path(self, route: str) -> tuple[str | None, dict[str, str]]:
        kwargs: dict[str, str] = {}
        path_name = None

        for path in self.__routes:
            l_route = path.strip('/').split('/')
            r_route = route.strip('/').split('/')

            if len(l_route) != len(r_route):
                continue

            if '{' in path and len(route) == 1:
                continue

            match = True

            for key, value in zip(l_route, r_route):
                if key.startswith('{') and key.endswith('}'):
                    kwargs[key[1:-1]] = value
                
                elif key != value:
                    match = False
                    kwargs.clear()
                    break

            if match:
                return path, kwargs
        
        return path_name, kwargs
    
    def launch_url(self, url: str) -> bool:
        return webbrowser.open(url=url)

    def set_cookie(
        self,
        cookie_name: str,
        cookie_value: str,
        path: str = '/',
        samesite: str = 'Strict',
        httponly: bool = True,
        secure: bool = True,
        expires: datetime = None
    ):
        cookie = f'{cookie_name}={cookie_value}; Path={path};'

        if httponly:
            cookie += ' HttpOnly;'
        
        if secure:
            cookie += ' Secure;'
        
        if samesite not in ['Strict', 'Lax', None]:
            raise AttributeError('Samsite is not valid. Please use one of the options: [Strict, Lax, None]')
        
        if expires and not isinstance(expires, datetime):
            raise ArithmeticError('Datetime is not valid, please use datetime to define the expires date.')

        if expires:
            expires_str = expires.strftime("%a, %d %b %Y %H:%M:%S GMT")
            cookie += f' Expires={expires_str};'
    
        cookie += f' SameSite={str(samesite)}'
        
        if cookie not in self.__cookies:
            self.__cookies.append(cookie)
    
    def update(self):
        return self.__update_handler()
    
    def run(self, target: Callable = None, **kwargs):
        from pyweber.models.run import run
        return run(target, **kwargs)
        
    @property
    def __serve_static_framework_files(self):
        self.__routes['/_pyweber/static/{uuid}/.js'] = str(StaticFilePath.js_base.value)
        self.__routes['/_pyweber/static/{uuid}/.css'] = str(StaticFilePath.pyweber_css.value)
        self.__routes['/_pyweber/static/favicon.ico'] = str(StaticFilePath.favicon_path.value.joinpath('favicon.ico'))

    async def __call__(self, scope, receive, send):
        from pyweber.models.run import run_as_asgi
        await run_as_asgi(scope, receive, send, app=self)
    
    async def __process_middleware(self, resp: Union[Request, Response], middle_list: list[dict[str, Union[int, Callable[..., Any]]]]):
        for middle_dict in middle_list:
            status_code, middle = middle_dict.values()
            params = inspect.signature(middle).parameters
            args, kwargs = [], {}

            for name, param in params.items():
                if param.kind in (inspect.Parameter.POSITIONAL_OR_KEYWORD, inspect.Parameter.KEYWORD_ONLY):
                    args.append(resp)
                elif param.kind == inspect.Parameter.KEYWORD_ONLY:
                    kwargs[name] = resp
            
            if inspect.iscoroutinefunction(middle):
                response = await middle(*args, **kwargs)
            else:
                response = middle(*args, **kwargs)

            if response:
                return status_code, response
    
    def __error_traceback(self):
        exc_type, exc_value, exc_traceback = sys.exc_info()
        error_details = traceback.format_exception(exc_type, exc_value, exc_traceback)
        error_message = ''.join(error_details)
        return error_message

    def __repr__(self):
        return f'Pyweber(routes={len(self.list_routes)}, window={self.window})'
    

class ResponseStruct:
    def __init__(self, content: Union[Template, str], status_code: int, content_type: ContentTypes, route: str):
        self.content = content
        self.status_code = status_code
        self.content_type = content_type
        self.route = route