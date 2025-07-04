from pyweber.core.template import Template
from pyweber.core.element import Element
from pyweber.utils.types import HTTPStatusCode, ContentTypes

import inspect
from string import punctuation
from pyweber.utils.exceptions import (
    InvalidRouteFormatError,
    RouteAlreadyExistError,
    RouteNotFoundError,
    RouteNameAlreadyExistError
)

from typing import Callable, Union

class RedirectRoute:
    def __init__(
        self,
        route: 'Route',
        status_code: int = 302,
        **kwargs
    ):
        self.route = route
        self.status_code = status_code
        self.kwargs = kwargs
    
    @property
    def route(self): return self.__route
    @property
    def status_code(self): return self.__status_code
    @property
    def kwargs(self): return self.__kwargs

    @route.setter
    def route(self, value: 'Route'):
        if not isinstance(value, Route):
            raise TypeError(f'{value}, must be a Route instances, but got {type(value).__name__}')
        
        self.__route = value
    
    @status_code.setter
    def status_code(self, value: int):
        if value not in self.redirected_status_code():
            raise ValueError(f'{value} must be an Redirect HttpStatusCode valid')
        
        self.__status_code = value
    
    @kwargs.setter
    def kwargs(self, value: dict[str, str]):
        if value and not isinstance(value, dict):
            raise TypeError(f'{value} must be a dict instances, but got {type(value).__name__}')
        
        self.__kwargs = value
    
    @staticmethod
    def redirected_status_code():
        return [code for code in HTTPStatusCode.code_list() if str(code).startswith('3')]
    
    def __repr__(self):
        return (
            f'RedirectRoute('
            f'route={self.route}, '
            f'status_code={self.status_code})'
        )

class Route:
    def __init__(
        self,
        route: str,
        template: Union[RedirectRoute, Template, Element, Callable, dict, str],
        group: str = None,
        methods: list[str] = None,
        name: str = None,
        middlewares: list[Callable] = None,
        status_code: int = None,
        content_type: ContentTypes = None,
        title: str = '',
        process_response: bool = True,
        **kwargs
    ):
        self.group = group
        self.route = route
        self.template = template
        self.methods = methods or self.default_method()
        self.name = name
        self.middlewares = middlewares or []
        self.status_code = status_code
        self.content_type = content_type or ContentTypes.html
        self.title = title
        self.process_response = process_response
        self.kwargs = kwargs
    
    @property
    def full_route(self): return f"/{self.group.removeprefix('__')}{self.route}" if self.group != self.default_group() else self.route
    
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
    def content_type(self): return self.__content_type

    @content_type.setter
    def content_type(self, value: ContentTypes):
        if not value:
            raise ValueError('content_type does not be a non empty')
        
        if not isinstance(value, ContentTypes):
            raise TypeError(f'content type must be a ContentTypes instances, but got {type(value).__name__}')
        
        self.__content_type = value
    
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
        self.__redirects: dict[str, RedirectRoute] = {}
        self.__route_names: dict[str, str] = {}
        self.groups: list[str] = []
    
    def is_redirected(self, route: str) -> bool:
        return self.get_redirected_route(route=route) is not None
    
    @property
    def default_group(self): return Route.default_group()

    @property
    def list_routes(self) -> list[str]:
        return [route.full_route for route in self.__routes.values() if '_pyweber' not in str(route.route)]
    
    @property
    def list_redirected_routes(self) -> list[str]:
        return list(self.__redirects.keys())
    
    def route_info(self, target: str):
        return self.get_route_by_name(name=target) or self.get_route_by_path(route=target)

    def clear_routes(self):
        """Remove all public routes. Routes that starts with __ are not removed"""
        for key, value  in self.__routes.items():
            if value.group and not str(value.group).startswith('__'):
                del self.__routes[key]

    def is_redirect_status_code(self, status_code: int):
        return status_code in RedirectRoute.redirected_status_code()

    def to_route(self, target: str, status_code: int = 302, **kwargs):
        if not self.is_redirect_status_code(status_code=status_code):
            raise ValueError(f'status code {status_code} is invalid Redirect HttpStatusCode')

        route = self.get_route_by_name(name=target) or self.get_route_by_path(route=target)
        if route:
            return RedirectRoute(route=route, status_code=status_code, **kwargs)
        
        raise RouteNotFoundError(route=target)

    def redirect(
        self,
        from_route: str,
        target: str,
        status_code: int=302,
        **kwargs
    ):
        route = self.get_route_by_name(name=target) or self.get_route_by_path(route=target)

        if not route:
            raise RouteNotFoundError(route=target)
        
        if not self.is_redirect_status_code(status_code=status_code):
            raise ValueError(f'status code {status_code} is invalid Redirect HttpStatusCode')
        
        self.__redirects[from_route] = RedirectRoute(route=route, status_code=status_code, **kwargs)

    def route(
        self,
        route: str,
        methods: list[str] = None,
        group: str = None,
        name: str = None,
        middlewares: list[str] = None,
        status_code: int = None,
        content_type: ContentTypes = None,
        title: str = None,
        process_response: bool = True
    ):
        def decorator(handler: Callable):
            async def wrapper(**kwargs):
                kwargs = self.validate_callable_args(handler, **kwargs)
                if inspect.iscoroutinefunction(handler):
                    response = await handler(**kwargs)

                else:
                    response = handler(**kwargs)
                
                self.__routes.get(route).template = response

                return self.__routes.get(route).template
            
            self.add_route(
                route=route,
                methods=methods,
                group=group,
                template=wrapper,
                name=name,
                middlewares=middlewares,
                status_code=status_code,
                content_type=content_type,
                title=title,
                process_response=process_response
            )
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
        status_code: int = None,
        content_type: ContentTypes = None,
        title: str = None,
        process_response: bool = True
    ):
        group = self.get_group(group=group)
        if self.full_route(route=route, group=group) in self.__routes:
            raise RouteAlreadyExistError(route=route)
        
        if self.get_route_by_name(name=name):
            raise RouteNameAlreadyExistError(name=name)
        
        _route = Route(
            route=route,
            group=group,
            template=template,
            methods=methods,
            name=name,
            middlewares=middlewares,
            status_code=status_code,
            content_type=content_type,
            title=title,
            process_response=process_response
        )

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
        full_route = self.full_route(route=route, group=group)
        _route = self.get_route_by_path(route=full_route)
        _kwargs = {}

        if not _route:
            raise RouteNotFoundError(route=full_route)

        route_by_name = self.get_route_by_name(name=kwargs.get('name', None))

        if route_by_name and route_by_name != _route:
            raise ValueError(f'Already exists a route with name {route_by_name.name}')
        
        for key, value in kwargs.items():
            if not hasattr(_route, key):
                _kwargs[key] = value
            
            if value:
                setattr(_route, key, value)
        
        if _kwargs:
            setattr(_route, kwargs, _kwargs)
    
    def remove_route(self, route: str, group: str = None):
        group = self.get_group(group=group)

        _r = self.__routes.get(self.full_route(route=route, group=group))

        if _r and '_pyweber' not in str(_r.route):
            del self.__routes[self.full_route(route=route, group=group)]
    
    def remove_group(self, group: str):
        for key, value in self.__routes.items():
            if group != self.default_group and group == value.group:
                del self.__routes[key]
    
    def remove_redirected_route(self, route: str):
        if route in self.__redirects:
            del self.__redirects[route]
    
    def get_route_by_path(self, route: str, follow_redirect: bool = True):
        path, _ = self.resolve_path(route=route)

        if follow_redirect in [True, 1] and self.is_redirected(route=path):
            redirect_route = self.get_redirected_route(route=path)
            return redirect_route.route
        return self.__routes.get(path)
    
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
        path, _ = self.resolve_path(route=route)
        return self.__redirects.get(path)
    
    def full_route(self, route: str, group: str):
        group = str(group).removeprefix('__') if group and group != self.default_group else ""
        return f'/{group}{route}' if group else route
    
    def get_group(self, group: str):
        return Route.get_group(group=group)
    
    def get_group_and_route(self, route: str):
        group = self.get_group_by_route(route=route)
        net_route = route.removeprefix(f'/{group}')
        return group, net_route
    
    def exists(self, route: str) -> bool:
        path, _ = self.resolve_path(route=route)
        return path in self.__routes or path in self.__redirects
    
    def resolve_path(self, route: str) -> tuple[str, dict[str, str]]:
        path, kwargs = self.__resolve_path__(route=route, list_routes=self.__redirects)

        if path not in self.__redirects:
            path, kwargs = self.__resolve_path__(route=route, list_routes=self.__routes)

        return path, kwargs
    
    @staticmethod
    def __resolve_path__(route: str, list_routes: dict[str, Route | RedirectRoute]):
        kwargs: dict[str, str] = {}

        for path in list_routes:
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
    
    @staticmethod
    def inspect_function(callback: Callable):
        sign = inspect.signature(obj=callback)
        params = sign.parameters

        return [{value.name: {
            'name': value.name,
            'default': value.default,
            'types': value.annotation,
            'kind': value.kind}
            } for _, value in params.items()
        ]
    
    @staticmethod
    def build_route(route: str, **kwargs):
        for name in kwargs:
            pattern = "{" + name + "}"
            route = route.replace(pattern, str(kwargs[name]))
        return route
    
    @staticmethod
    def validate_callable_args(callback: Callable, **kwargs):
        sig = inspect.signature(callback)
        bound_args = {}
        extra_args = []
        extra_kwargs = {}
        name_args, name_kwargs = None, None

        normal_params = [p.name for p in sig.parameters.values()
                         if p.kind in (inspect.Parameter.POSITIONAL_OR_KEYWORD, inspect.Parameter.POSITIONAL_ONLY)]

        for name, param in sig.parameters.items():

            if param.kind == inspect.Parameter.VAR_POSITIONAL:

                if name in kwargs:
                    extra_args = kwargs[name]

                    if not isinstance(extra_args, (list, tuple)):
                        raise TypeError(f'Argument for {name} must be a list ou tuple instances')
                else:
                    extra_args = []
                
                name_args = name
            
            elif param.kind == inspect.Parameter.VAR_KEYWORD:
                for k, v in kwargs.items():
                    if k not in normal_params and k != name:
                        extra_kwargs[k] = v
                
                name_kwargs = name
            
            else:
                if name in kwargs:
                    bound_args[name] = kwargs[name]
                elif param.default is not inspect.Parameter.empty:
                    bound_args[name] = param.default
                else:
                    raise TypeError(f"{callback.__name__}() missing required positional argument: {name}")
        
        if extra_args:
            bound_args[name_args] = extra_args
        
        if extra_kwargs:
            bound_args[name_kwargs] = extra_kwargs

        return bound_args