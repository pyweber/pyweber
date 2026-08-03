import re
import inspect
from string import punctuation
from typing import Callable, Union, Any

from pyweber.core.template import Template
from pyweber.core.element import Element
from pyweber.utils.types import HTTPStatusCode, ContentTypes
from pyweber.utils.exceptions import (
    InvalidRouteFormatError,
    RouteAlreadyExistError,
    RouteNotFoundError,
    RouteNameAlreadyExistError
)

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
        callback: Callable[..., Any] = None,
        tags: list[str] = None,
        description: str = None,
        responses: dict = None,
        response_model: Any = None,
        security: list = None,
        deprecated: bool = False,
        include_in_schema: bool = True,
        operation_id: str = None,
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
        self.callback = callback
        self.tags = list(tags) if tags else []
        self.description = description
        self.responses = dict(responses) if responses else {}
        self.response_model = response_model
        self.security = security  # None inherits global; [] = public
        self.deprecated = bool(deprecated)
        self.include_in_schema = include_in_schema if include_in_schema is not None else True
        self.operation_id = operation_id
        self.kwargs = kwargs

    @property
    def route_with_params(self): return self.__route_with_params

    @property
    def query_params(self): return self.__query_params

    @property
    def callback(self): return self.__callback

    @callback.setter
    def callback(self, callback: Callable[..., Any]):
        if callback:
            assert callable(callback)

        self.__callback = callback or self.template if callable(self.template) else lambda **kwargs: self.template

    @property
    def full_route(self):
        return f"/{self.group.removeprefix('__')}{self.route}" if self.group != self.default_group() else self.route

    @property
    def full_route_with_params(self):
        return f"{self.full_route}{('?' + self.route_with_params.split('?',1)[-1] if self.query_params else '')}"

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

        path, _, query_str = value.partition('?')
        self.__query_params = self.__parse_and_validate_query(query_str) if query_str else []
        self.__route = path.removesuffix('/') if len(path) > 1 else path
        self.__route_with_params = value

    @staticmethod
    def __parse_and_validate_query(query_str: str) -> list[str]:
        """Valida e extrai os nomes dos query params"""
        pairs = query_str.split('&')
        keys = []

        for pair in pairs:
            if '=' not in pair:
                raise InvalidRouteFormatError(f'Query params must follow the format ?key={key}&key={key}')

            key, _, placeholder = pair.partition('=')

            # key e placeholder não podem ser vazios
            if not key or not placeholder:
                raise InvalidRouteFormatError('Query param key or placeholder cannot be empty')

            # placeholder deve estar no formato {key}
            if not (placeholder.startswith('{') and placeholder.endswith('}')):
                raise InvalidRouteFormatError(f"Query param '{key}' value must be a placeholder like {{{key}}}, got '{placeholder}'")

            # nome dentro do placeholder deve ser igual à key
            param_name = placeholder[1:-1]
            if param_name != key:
                raise InvalidRouteFormatError(f"Query param key and placeholder must match: '{key}' != '{param_name}'")

            # key não pode ter caracteres especiais
            if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', key):
                raise InvalidRouteFormatError(f"Query param key '{key}' contains invalid characters")

            if key in keys:
                raise InvalidRouteFormatError(f"Duplicate query param key '{key}'")

            keys.append(key)

        return keys

    @staticmethod
    def paramaters_types():
        return {'int': 'integer', 'str': 'string', 'float': 'number'}

    @staticmethod
    def argument_types():
        return {
            **Route.paramaters_types(),
            'list': 'array',
            'dict': 'object',
            'set': 'array',
            'tuple': 'array'
        }

    @classmethod
    def get_callback_parameters(cls, callback: Callable[..., Any]):
        sign = inspect.signature(obj=callback)
        params = sign.parameters

        return {param.name: {
                    "default": param.default,
                    "types": param.annotation,
                } for _, param in params.items()}

    @classmethod
    def get_query_parameters(cls, route: str, callback: Callable):
        assert isinstance(route, str)
        pattern = r'{\s*(.*?)\s*}'
        params_list = re.findall(pattern, route)
        params: dict[str, dict[str, dict[str, Any]]] = {"parameters": {}, "body": {}}

        callback_parameters = cls.get_callback_parameters(callback)

        for param in params_list:
            if param in callback_parameters:
                params['parameters'][param] = {}
                _types = callback_parameters[param].get('types')
                default = callback_parameters[param].get('default')

                params['parameters'][param]['type'] = Route.paramaters_types().get(_types.__name__, 'string')
                params['parameters'][param]['required'] = True if default == inspect._empty else False
                params['parameters'][param]['default'] = default

            else:
                params['parameters'][param] = {
                    'type': 'string',
                    'default': inspect._empty,
                    'required': True
                }

        if callback.__name__ != '<lambda>':
            parameters = {key: value for key, value in callback_parameters.items() if key not in params_list}

            if parameters:
                body = {
                    "description": "",
                    "required": True,
                    "content": {
                        ContentTypes.json.value: {
                            "schema": {
                                "type": 'object',
                                "required": [param for param, val in parameters.items() if val != inspect._empty],
                                "properties": {
                                    param: {
                                        "default": callback_parameters[param].get(
                                            'default'
                                        ) if callback_parameters[param].get('default') != inspect._empty else None,
                                        'type': Route.argument_types().get(
                                            callback_parameters[param].get('types').__name__,
                                            'string'
                                        )
                                    } for param, value in parameters.items()
                                }
                            }
                        }
                    }
                }

                params['body'] = body

        return params

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
            f'route_with_params={self.route_with_params}, '
            f'name={self.name}, '
            f'methods={self.methods}, '
            f'status_code={self.status_code})'
        )

class RouteManager:
    def __init__(self):
        # path -> list of Route (same path may have different HTTP methods)
        self.__routes: dict[str, list[Route]] = {}
        self.__redirects: dict[str, RedirectRoute] = {}
        # name -> (path, methods)
        self.__route_names: dict[str, tuple[str, tuple[str, ...]]] = {}
        # Insertion-ordered dynamic path keys (contain ``{param}``) for O(k) matching
        self.__dynamic_route_paths: list[str] = []
        self.__dynamic_redirect_paths: list[str] = []
        self.groups: list[str] = []

    @staticmethod
    def _is_dynamic_path(path: str) -> bool:
        return '{' in (path or '')

    def _index_route_path(self, path: str):
        if self._is_dynamic_path(path) and path not in self.__dynamic_route_paths:
            self.__dynamic_route_paths.append(path)

    def _unindex_route_path(self, path: str):
        if path in self.__dynamic_route_paths:
            self.__dynamic_route_paths.remove(path)

    def _index_redirect_path(self, path: str):
        if self._is_dynamic_path(path) and path not in self.__dynamic_redirect_paths:
            self.__dynamic_redirect_paths.append(path)

    def _unindex_redirect_path(self, path: str):
        if path in self.__dynamic_redirect_paths:
            self.__dynamic_redirect_paths.remove(path)

    def is_redirected(self, route: str) -> bool:
        return self.get_redirected_route(route=route) is not None

    @property
    def default_group(self): return Route.default_group()

    @property
    def list_routes(self) -> list[str]:
        return [
            path for path, routes in self.__routes.items()
            if routes and '_pyweber' not in str(routes[0].route)
        ]

    @property
    def list_redirected_routes(self) -> list[str]:
        return list(self.__redirects.keys())

    def route_info(self, target: str):
        return self.get_route_by_name(name=target) or self.get_route_by_path(route=target)

    def clear_routes(self):
        """Remove all public routes. Routes that starts with __ are not removed"""
        keys_to_remove = [
            key for key, routes in self.__routes.items()
            if routes and routes[0].group and not str(routes[0].group).startswith('__')
        ]
        for key in keys_to_remove:
            del self.__routes[key]
            self._unindex_route_path(key)

    def get_allowed_methods(self, route: str) -> list[str]:
        """Return all HTTP methods registered for a resolved path."""
        path, _ = self.resolve_path(route=route)
        methods: list[str] = []
        for registered in self.__routes.get(path, []):
            methods.extend(registered.methods)
        return methods

    def get_routes_by_path(self, route: str, follow_redirect: bool = True) -> list[Route]:
        """Return all Route objects registered for a path."""
        path, _ = self.resolve_path(route=route)

        if follow_redirect in [True, 1] and self.is_redirected(route=path):
            redirect_route = self.get_redirected_route(route=path)
            return [redirect_route.route] if redirect_route else []

        return list(self.__routes.get(path, []))

    def _method_overlap(self, existing: list[Route], methods: list[str]) -> list[str]:
        wanted = {m.upper() for m in methods}
        overlap: list[str] = []
        for registered in existing:
            overlap.extend(sorted(wanted & {m.upper() for m in registered.methods}))
        return overlap

    def is_redirect_status_code(self, status_code: int):
        return status_code in RedirectRoute.redirected_status_code()

    def to_route(self, target: str, status_code: int = 302, **kwargs):
        if not self.is_redirect_status_code(status_code=status_code):
            raise ValueError(f'status code {status_code} is invalid Redirect HttpStatusCode')

        route = self.get_route_by_name(target)

        if not route:
            route = self.get_route_by_path(target)

            if route:
                _, kwd = self.resolve_path(target)

                kwargs = {**kwargs, **kwd}

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
        self._index_redirect_path(from_route)

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
        process_response: bool = True,
        tags: list[str] = None,
        description: str = None,
        responses: dict = None,
        response_model: Any = None,
        security: list = None,
        deprecated: bool = False,
        include_in_schema: bool = True,
        operation_id: str = None,
    ):
        def decorator(handler: Callable[..., Union[Template, Element, str, dict, list]]):
            async def wrapper(**kwargs):
                kwargs = self.validate_callable_args(handler, **kwargs)
                if inspect.iscoroutinefunction(handler):
                    response = await handler(**kwargs)

                else:
                    response = handler(**kwargs)
                return response

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
                process_response=process_response,
                callback=handler,
                tags=tags,
                description=description,
                responses=responses,
                response_model=response_model,
                security=security,
                deprecated=deprecated,
                include_in_schema=include_in_schema,
                operation_id=operation_id,
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
        process_response: bool = True,
        tags: list[str] = None,
        description: str = None,
        responses: dict = None,
        response_model: Any = None,
        security: list = None,
        deprecated: bool = False,
        include_in_schema: bool = True,
        operation_id: str = None,
        **kwargs
    ):

        group = self.get_group(group=group)
        full = self.full_route(route=route, group=group)
        existing = self.__routes.get(full, [])

        if not callable(template):
            template = (lambda static: lambda **kwargs: static)(template)

        handler = kwargs.get('callback', None) or template

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
            process_response=process_response,
            callback=handler,
            tags=tags,
            description=description,
            responses=responses,
            response_model=response_model,
            security=security,
            deprecated=deprecated,
            include_in_schema=include_in_schema,
            operation_id=operation_id,
        )

        overlap = self._method_overlap(existing, _route.methods)
        if overlap:
            raise RouteAlreadyExistError(route=route, methods=overlap)

        if name and self.get_route_by_name(name=name):
            raise RouteNameAlreadyExistError(name=name)

        self.__routes.setdefault(full, []).append(_route)
        self._index_route_path(full)
        if name:
            self.__route_names[name] = (full, tuple(_route.methods))

    def add_group_routes(self, routes: list[Route], group: str = None):
        group = self.get_group(group=group)

        if not all(isinstance(route, Route) for route in routes):
            raise TypeError(f'All routes must be Route instances')

        for route in routes:
            route.group = group
            full = route.full_route
            existing = self.__routes.get(full, [])
            overlap = self._method_overlap(existing, route.methods)
            if overlap:
                # Internal re-registration replaces entries that share methods.
                self.__routes[full] = [
                    r for r in existing
                    if not (set(r.methods) & set(route.methods))
                ]
            self.__routes.setdefault(full, []).append(route)
            self._index_route_path(full)
            if route.name:
                self.__route_names[route.name] = (full, tuple(route.methods))

    def update_route(self, route: str, group: str=None, method: str = None, **kwargs):
        full_route = self.full_route(route=route, group=group)
        _route = self.get_route_by_path(route=full_route, method=method)

        if not _route:
            raise RouteNotFoundError(route=full_route)

        route_by_name = self.get_route_by_name(name=kwargs.get('name', None))

        if route_by_name and route_by_name != _route:
            raise ValueError(f'Already exists a route with name {route_by_name.name}')

        known = {
            'template', 'methods', 'name', 'middlewares', 'status_code', 'content_type',
            'title', 'process_response', 'callback', 'tags', 'description', 'responses',
            'response_model', 'security', 'deprecated', 'include_in_schema', 'operation_id',
            'group', 'route',
        }
        extra = {}
        for key, value in kwargs.items():
            if key in known and hasattr(_route, key):
                if value is not None and value != '':
                    setattr(_route, key, value)
            else:
                extra[key] = value

        if extra:
            merged = dict(getattr(_route, 'kwargs', None) or getattr(_route, 'kwargs', {}) or {})
            # Route stores free-form kwargs on .kwargs
            current = dict(_route.kwargs or {})
            current.update(extra)
            _route.kwargs = current

    def remove_route(self, route: str, group: str = None, methods: list[str] = None):
        group = self.get_group(group=group)
        full = self.full_route(route=route, group=group)
        registered = self.__routes.get(full)

        if not registered:
            return

        if '_pyweber' in str(registered[0].route):
            return

        if methods:
            wanted = {m.upper() for m in methods}
            remaining = [
                r for r in registered
                if not (set(r.methods) & wanted)
            ]
            if remaining:
                self.__routes[full] = remaining
            else:
                del self.__routes[full]
                self._unindex_route_path(full)
        else:
            del self.__routes[full]
            self._unindex_route_path(full)

    def remove_group(self, group: str):
        keys_to_remove = [
            key for key, routes in self.__routes.items()
            if routes and group != self.default_group and group == routes[0].group
        ]
        for key in keys_to_remove:
            del self.__routes[key]
            self._unindex_route_path(key)

    def remove_redirected_route(self, route: str):
        if route in self.__redirects:
            del self.__redirects[route]
            self._unindex_redirect_path(route)

    def get_route_by_path(self, route: str, follow_redirect: bool = True, method: str = None):
        path, _ = self.resolve_path(route=route)

        if follow_redirect in [True, 1] and self.is_redirected(route=path):
            redirect_route = self.get_redirected_route(route=path)
            return redirect_route.route if redirect_route else None

        routes = self.__routes.get(path, [])
        if not routes:
            return None

        if method:
            method = str(method).upper()
            for registered in routes:
                if method in registered.methods:
                    return registered
            return None

        return routes[0]

    def get_route_by_name(self, name: str):
        if not name or name not in self.__route_names:
            return None

        path, methods = self.__route_names[name]
        routes = self.__routes.get(path, [])
        method_set = set(methods)
        for registered in routes:
            if method_set & set(registered.methods):
                return registered
        return routes[0] if routes else None

    def get_group_routes(self, group: str = None):
        group = self.get_group(group=group)
        return [
            route
            for routes in self.__routes.values()
            for route in routes
            if group == route.group
        ]

    def get_group_by_route(self, route: str):
        routes = self.__routes.get(route)
        if routes:
            return routes[0].group
        return None

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
        path, kwargs = self.__resolve_path__(
            route=route,
            list_routes=self.__redirects,
            dynamic_paths=self.__dynamic_redirect_paths,
        )

        if path not in self.__redirects:
            path, kwargs = self.__resolve_path__(
                route=route,
                list_routes=self.__routes,
                dynamic_paths=self.__dynamic_route_paths,
            )

        return path, kwargs

    @staticmethod
    def __resolve_path__(
        route: str,
        list_routes: dict,
        dynamic_paths: list[str] | None = None,
    ):
        kwargs: dict[str, str] = {}

        # Separa path dos query params antes de qualquer processamento
        clean_route, _, query_string = route.partition('?')

        # Parse dos query params
        query_params: dict[str, str] = {}
        if query_string:
            for pair in query_string.split('&'):
                key, _, val = pair.partition('=')
                if key:
                    query_params[key] = val

        # O(1) exact match for static paths (and dynamic keys requested verbatim)
        if clean_route in list_routes:
            return clean_route, query_params

        # Scan only dynamic patterns (paths containing ``{param}``)
        paths_to_scan = (
            dynamic_paths
            if dynamic_paths is not None
            else [p for p in list_routes if '{' in p]
        )

        for path in paths_to_scan:
            if path not in list_routes:
                continue

            l_route = path.strip('/').split('/')
            r_route = clean_route.strip('/').split('/')  # usa o path limpo

            if len(l_route) != len(r_route):
                continue

            if '{' in path and len(clean_route) == 1:
                continue

            match = True
            kwargs.clear()

            for key, value in zip(l_route, r_route):
                if key.startswith('{') and key.endswith('}'):
                    kwargs[key[1:-1]] = value

                elif key != value:
                    match = False
                    kwargs.clear()
                    break

            if match:
                return path, {**kwargs, **query_params}  # merge kwargs + query_params

        return clean_route, query_params

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
