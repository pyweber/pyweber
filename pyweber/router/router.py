from pyweber.core.template import Template
from pyweber.router.response import ResponseBuilder
from pyweber.utils.load import StaticTemplates, LoadStaticFiles
from pyweber.router.request import Request
from pyweber.utils.exceptions import *
from pyweber.router.request import Request
from pyweber.utils.types import ContentTypes, StaticFilePath
import webbrowser
import requests
from datetime import datetime

class Router:
    def __init__(self, update_handler: callable):
        self.__routes: dict[str, Template] = {}
        self.__redirects: dict[str, str] = {}
        self.__update_handler = update_handler
        self.__page_not_found = Template(template=StaticTemplates.PAGE_NOT_FOUND(), status_code=404)
        self.__page_unauthorized = Template(template=StaticTemplates.PAGE_UNAUTHORIZED(), status_code=401)
        self.__middleware: list[callable] = []
        self.__cookies: list[str] = []
        self.__serve_static_framework_files
    
    @property
    def list_routes(self) -> list[str]:
        return [key for key in self.__routes if '_pyweber' not in key]
    
    @property
    def clear_routes(self) -> None:
        self.__routes.clear()
    
    @property
    def page_not_found(self):
        return self.__page_not_found
    
    @property
    def page_unauthorized(self):
        return self.__page_unauthorized
    
    @page_unauthorized.setter
    def page_unauthorized(self, template: Template):
        if not isinstance(template, Template):
            raise InvalidTemplateError()

        self.page_unauthorized = template
    
    @page_not_found.setter
    def page_not_found(self, template: Template):
        if not isinstance(template, Template):
            raise InvalidTemplateError()

        self.__page_not_found = template
    
    @property
    def cookies(self):
        return self.__cookies
    
    def middleware(self, middle_func: callable):
        self.__middleware.append(middle_func)
        return middle_func
    
    @property
    def clear_middleware(self):
        return self.__middleware.clear()
    
    def route(self, route: str):
        def decorator(func):
            template = func()
            if not isinstance(template, Template):
                raise InvalidTemplateError()
            
            self.add_route(route=route, template=template)
            return func
        
        return decorator
    
    def add_route(self, route: str, template: Template) -> None:

        if not route.startswith('/'):
            raise InvalidRouteFormatError()
        
        elif route in self.__routes:
            raise RouteAlreadyExistError(route=route)
        
        elif not isinstance(template, Template):
            raise InvalidTemplateError()
        
        self.__routes[route] = template
    
    def update_route(self, route: str, template: Template) -> None:
        if route not in self.__routes:
            raise RouteNotFoundError(route=route)
        elif not isinstance(template, Template):
            raise InvalidTemplateError()
        self.__routes[route] = template

    def remove_route(self, route: str) -> None:
        if route not in self.__routes:
            raise RouteNotFoundError(route=route)
        del self.__routes[route]

    def redirect(self, from_route: str, to_route: str) -> None:
        if to_route not in self.__routes:
            raise RouteNotFoundError(route=to_route)
        self.__redirects[from_route] = to_route
    
    def get_route(self, request: Request):

        for middleware in self.__middleware:
            response: Template = middleware(request)

            if response:
                return ResponseBuilder(
                    request=request,
                    response_content=response.build_html().encode(),
                    code=response.status_code,
                    cookies=self.cookies,
                    response_type=self.get_content_type(request=request),
                    route=request.path
                ).build_respose
        
        if request.netloc:
            req = requests.request(method='GET', url=request.get_url)

            return ResponseBuilder(
                request=request,
                response_content=req.content,
                code=req.status_code,
                response_type=self.get_content_type(request=request),
                cookies=self.cookies,
                route=request.get_url
            ).build_respose
        
        if '.' in request.path.split('/')[-1]:
            try:
                if request.path in self.__routes:
                    resp = LoadStaticFiles(self.__routes.get(request.path)).load
                else:
                    resp = LoadStaticFiles(request.path).load

                return ResponseBuilder(
                    request=request,
                    response_content=resp.encode() if isinstance(resp, str) else resp,
                    code=200,
                    response_type=self.get_content_type(request=request),
                    cookies=self.cookies,
                    route=request.path
                ).build_respose
    
            except FileNotFoundError:
                return ResponseBuilder(
                    request=request,
                    response_content=b'File not found',
                    code=404,
                    cookies=self.cookies,
                    response_type=ContentTypes.html,
                    route=request.path
                ).build_respose
        
        if request.path in self.__redirects:
            route = self.get_redirected_route(route=request.path)
            template = self.get_template(request.path)
            template.status_code = 302 if template.status_code == 200 else template.status_code
            return ResponseBuilder(
                request=request,
                response_content=template.build_html().encode(),
                code=template.status_code,
                cookies=self.cookies,
                response_type=self.get_content_type(request=request),
                route=route
            ).build_respose
        
        if request.path not in self.__routes:
            return ResponseBuilder(
                request=request,
                response_content=self.get_template(request.path).build_html().encode(),
                code=self.get_template(route=request.path).status_code,
                cookies=self.cookies,
                response_type=self.get_content_type(request=request),
                route=request.path
            ).build_respose
        
        template = self.get_template(request.path)
        template.status_code = 200 if template.status_code != 200 else template.status_code
        return ResponseBuilder(
            request=request,
            response_content=self.get_template(request.path).build_html().encode(),
            code=self.get_template(route=request.path).status_code,
            cookies=self.cookies,
            response_type=self.get_content_type(request=request),
            route=request.path
        ).build_respose
    
    def get_redirected_route(self, route: str) -> str:
        return self.__redirects[route]
    
    def get_template(self, route: str):
        if route in self.__routes or self.is_redirected(route=route):
            if self.is_redirected(route=route):
                return self.__routes[self.__redirects[route]]
            
            return self.__routes[route]
        
        return self.page_not_found
    
    def get_content_type(self, request: Request) -> ContentTypes:
        path = request.path
        l_text = path.split('/')[-1]

        if '.' in l_text:
            extension = l_text.split('.')[-1].strip()

            for ext in ContentTypes:
                if extension == ext.name:
                    return ext
        
            return ContentTypes.unkown
        
        return ContentTypes.html
    
    def exists(self, route: str) -> bool:
        return route in self.__routes
    
    def is_redirected(self, route: str) -> bool:
        return route in self.__redirects
    
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
        cookie = f'Set-Cookie: {cookie_name}={cookie_value}; Path={path}'

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
    
        cookie += f' SameSite={str(samesite)}\r\n'
        
        if cookie not in self.__cookies:
            self.__cookies.append(cookie)
    
    def update(self):
        return self.__update_handler()
    
    @property
    def __serve_static_framework_files(self):
        self.__routes['/_pyweber/static/js.js'] = str(StaticFilePath.js_base.value)
        self.__routes['/_pyweber/static/favicon.ico'] = str(StaticFilePath.favicon_path.value.joinpath('favicon.ico'))