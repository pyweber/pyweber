from pyweber.core.template import Template
from pyweber.core.element import Element
from pyweber.utils.types import HTTPStatusCode

import inspect
from string import punctuation
from pyweber.utils.exceptions import (
    InvalidRouteFormatError,
    RouteAlreadyExistError,
    RouteNotFoundError
)

from typing import Callable, Union

class Route:
    def __init__(
        self,
        route: str,
        template: Union[Template, Element, Callable, dict, str],
        group: str = None,
        methods: list[str] = None,
        name: str = None,
        middlewares: list[Callable] = None,
        status_code: int = None,
        **kwargs
    ):
        self.group = group
        self.route = route
        self.template = template
        self.methods = methods or self.default_method()
        self.name = name
        self.middlewares = middlewares or []
        self.status_code = status_code
    
    @property
    def full_route(self): return f'/{self.group.removeprefix('__')}{self.route}' if self.group != self.default_group() else self.route
    
    @property
    def template(self): return self.__template

    @template.setter
    def template(self, value: Union[Template, Element, Callable, dict, str]):
        if not value:
            raise ValueError('Template does not be an empty value')
        
        self.__template = value
    
    @property
    def middlewares(self): return self.__middlewares

    @middlewares.setter
    def middlewares(self, middlewares: list[Callable]):
        if not isinstance(middlewares, list):
            raise TypeError(f'middlewares must be a list instances, but got {type(middlewares).__name__}')
        
        if middlewares and not all(callable(middleware) for middleware in middlewares):
            raise ValueError('All middlewares must but be a Callable functions')

        self.__middlewares = middlewares
    
    @property
    def methods(self): return self.__methods

    @methods.setter
    def methods(self, methods: list[str]):
        if not isinstance(methods, list):
            raise TypeError(f'methods must be a list instances, but got {type(methods).__name__}')
        
        if methods and not all(str(method).upper() in self.allowed_methods() for method in methods):
            raise ValueError(f'All methods must be inclued in {self.allowed_methods()}')

        self.__methods = [method.upper() for method in methods]
    
    @property
    def status_code(self): return self.__status_code

    @status_code.setter
    def status_code(self, value: int):
        if not value:
            value = 200
        
        if value not in HTTPStatusCode.code_list():
            raise ValueError('The status must be a HttpStatusCode valid')
        
        self.__status_code = value
    
    @property
    def group(self): return self.__group

    @group.setter
    def group(self, value: str):
        group = Route.get_group(group=value)

        if any(symb in str(group) for symb in str(punctuation).replace('_', '')):
            raise ValueError('Symbols is not alloweds in the group name')
        
        self.__group = value
    
    @property
    def route(self): return self.__route

    @route.setter
    def route(self, value: str):
        value = str(value)

        if not value.startswith('/'):
            raise InvalidRouteFormatError()
        
        self.__route = value

    @staticmethod
    def get_group(group: str):
        return group or Route.default_group()
    
    @staticmethod
    def default_group():
        return '__pyweber'
    
    @staticmethod
    def default_method():
        return ['GET']
    
    @staticmethod
    def allowed_methods():
        return ['GET', 'POST', 'PATCH', 'PUT', 'DELETE', 'HEAD', 'OPTIONS']
    
    def __repr__(self):
        return (
            f'Route('
            f'group={self.group}, '
            f'route={self.route}, '
            f'full_route={self.full_route}, '
            f'name={self.name}, '
            f'methods={self.methods}, '
            f'status_code={self.status_code})'
        )

class RouteManager:
    def __init__(self):
        self.__routes: dict[str, Route] = {}
        self.__redirects: dict[str, dict[str, str]] = {}
        self.__route_names: dict[str, str] = {}
        self.groups: list[str] = []
    
    def is_redirected(self, route: str) -> bool: return self.__redirects.get(route) is not None
    
    @property
    def default_group(self): return Route.default_group()

    @property
    def list_routes(self) -> list[str]:
        return [route for route in list(self.__routes.keys()) if not str(route).startswith('__')]
    
    def route_info(self, route: str, group: str = None):
        return self.__routes.get(self.full_route(route=route, group=group))

    def clear_routes(self):
        """Remove all public routes. Routes that starts with __ are not removed"""
        for key, value  in self.__routes.items():
            if value.group and not str(value.group).startswith('__'):
                del self.__routes[key]
    
    def redirect(self, from_route: str, to_route: str, group: str = None):
        group = self.get_group(group=group)
        
        if self.full_route(route=to_route, group=group) not in self.__routes:
            raise RouteNotFoundError(route=to_route)
        
        self.__redirects[from_route] = {group: to_route}
    
    def route(self, route: str, methods: list[str] = None, group: str = None, name: str = None, middlewares: list[str] = None, status_code: int = None):
        def decorator(handler: Callable):
            async def wrapper(**kwargs):
                if inspect.iscoroutinefunction(handler):
                    response = await handler(**kwargs)

                else:
                    response = handler(**kwargs)

                # self.update_route(route=route, template=response)

                return response
            
            self.add_route(route=route, methods=methods, template=wrapper, name=name, middlewares=middlewares, status_code=status_code)
            return wrapper
        return decorator
    
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
        group = self.get_group(group=group)
        if self.full_route(route=route, group=group) in self.__routes:
            raise RouteAlreadyExistError(route=route)
        
        if self.get_route_by_name(name=name):
            raise ValueError(f'Already exists a route with name {name}')
        
        _route = Route(route=route, group=group, template=template, methods=methods, name=name, middlewares=middlewares, status_code=status_code)

        self.__routes[_route.full_route] = _route
        if name: self.__route_names[name] = _route.full_route
    
    def add_group_routes(self, routes: list[Route], group: str = None):
        group = self.get_group(group=group)

        if not all(isinstance(route, Route) for route in routes):
            raise TypeError(f'All routes must be Route instances')
        
        for route in routes:
            route.group = group
            self.__routes[route.full_route] = route
    
    def update_route(self, route: str, group: str=None, **kwargs):
        _route = self.__routes.get(self.full_route(route=route, group=group))

        if _route:
            route_info = {
                'name': kwargs.get('name'),
                'template': kwargs.get('template'),
                'group': kwargs.get('group'),
                'methods': kwargs.get('methods'),
                'middlewares': kwargs.get('middlewares'),
                'status_code': kwargs.get('status_code')
            }

            route_by_name = self.get_route_by_name(name=route_info.get('name'))

            if route_by_name and route_by_name != _route:
                raise ValueError(f'Already exists a route with name {route_by_name.name}')
            
            if route_info.get('template'):
                _route.template = route_info.get('template')
    
    def remove_route(self, route: str, group: str = None):
        group = self.get_group(group=group)

        if self.__routes.get(self.full_route(route=route, group=group)):
            del self.__routes[self.full_route(route=route, group=group)]
    
    def remove_group(self, group: str):
        for key, value in self.__routes.items():
            if group != self.default_group and group == value.group:
                del self.__routes[key]
    
    def remove_redirected_route(self, route: str):
        if route in self.__redirects:
            del self.__redirects[route]
    
    def get_route_by_path(self, route: str):
        if self.is_redirected(route=route):
            key, value = self.get_redirected_route(route=route).items()
            return self.__routes.get(self.full_route(route=value, group=key))
        return self.__routes.get(route)
    
    def get_route_by_name(self, name: str):
        return self.__routes[self.__route_names[name]] if name in self.__route_names else None
    
    def get_group_routes(self, group: str = None):
        group = self.get_group(group=group)
        return [value for _, value in self.__routes.items() if group == value.group]
    
    def get_group_by_route(self, route: str):
        if route in self.__routes:
            for key, value in self.__routes.items():
                if key == route:
                    return value.group
    
    def get_redirected_route(self, route: str):
        return self.__redirects.get(route)
    
    def full_route(self, route: str, group: str):
        group = str(group).removeprefix('__') if group and group != self.default_group else ""
        return f'/{group}{route}' if group else route
    
    def get_group(self, group: str):
        return Route.get_group(group=group)
    
    def exists(self, route: str) -> bool:
        route, _ = self.resolve_path(route=route)
        return route in self.__routes
    
    def resolve_path(self, route: str) -> tuple[str, str | None, dict[str, str]]:
        kwargs: dict[str, str] = {}
        group = self.get_group_by_route(route=route)
        group = self.get_group(group=group)

        if self.full_route(route=route, group=group) in self.__redirects:
            return route, kwargs

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
        
        return route, kwargs