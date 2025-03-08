from pyweber.core.template import Template
from pyweber.utils.load import StaticTemplates
from pyweber.utils.exceptions import *

class Router:
    def __init__(self, update_handler: callable):
        self.__routes: dict[str, Template] = {}
        self.__redirects: dict[str, str] = {}
        self.__update_handler = update_handler
        self.__page_not_found = Template(template=StaticTemplates.PAGE_NOT_FOUND())
        self.__page_unauthorized = Template(template=StaticTemplates.PAGE_UNAUTHORIZED())
    
    @property
    def list_routes(self) -> list[str]:
        return list(self.__routes.keys())
    
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

        self.__page_not_found = template
    
    @page_not_found.setter
    def page_not_found(self, template: Template):
        if not isinstance(template, Template):
            raise InvalidTemplateError()

        self.__page_not_found = template
    
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
    
    def redirect(self, from_route: str, to_route: str) -> str:
        if to_route not in self.__routes:
            raise RouteNotFoundError(route=to_route)
        
        self.__redirects[from_route] = to_route
    
    def get_route(self, route: str) -> Template:
        if route in self.__redirects:
            route = self.__redirects[route]
        
        if route not in self.__routes:
            raise RouteNotFoundError(route=route)
        
        return self.__routes[route]
    
    def get_redirected_route(self, route: str) -> str:
        return self.__redirects[route]
    
    def exists(self, route: str) -> bool:
        return route in self.__routes
    
    def is_redirected(self, route: str) -> bool:
        return route in self.__redirects
    
    def update(self):
        return self.__update_handler()