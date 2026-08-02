from typing import Callable, Union, Any
from dataclasses import dataclass
import inspect
from pyweber.models.request import Request
from pyweber.models.response import Response
from pyweber.core.element import Element
from pyweber.core.template import Template
from pyweber.utils.types import HTTPStatusCode
from pyweber.utils.deprecation import warn_deprecated
from pyweber.models.routes import RouteManager

@dataclass
class MiddlewareResult:
    status_code: int
    process_response: bool
    content: Union[Template, Element, Response, dict, str]

class MiddlewareManager:
    def __init__(self):
        self.__before_request: list[dict[str, Union[int, Callable, bool]]] = []
        self.__after_request: list[dict[str, Union[int, Callable, bool]]] = []
        self.__onion: list[dict[str, Any]] = []

    @property
    def get_before_request_middlewares(self):
        return self.__before_request

    @property
    def get_after_request_middlewares(self):
        return self.__after_request

    @property
    def get_onion_middlewares(self):
        return self.__onion

    def before_request(
        self,
        fn: Callable | None = None,
        *,
        status_code: int = 200,
        process_response: bool = True,
        order: int = -1,
    ):
        """Flask-style hook: ``(request) -> None | body``.

        Use as ``@app.before_request`` or ``@app.before_request()``.
        Returning ``None`` continues; any other value short-circuits the route.
        """
        if status_code != 200 or process_response is not True:
            warn_deprecated(
                'before_request(status_code=..., process_response=...)',
                alternative='return a Response/Template with the desired status from the hook',
                removal='2.0',
            )

        def register(middleware: Callable[..., Any]):
            self.add_before_request(
                middleware,
                status_code=status_code,
                process_response=process_response,
                order=order,
            )
            return middleware

        if fn is not None and callable(fn):
            return register(fn)
        return register

    def after_request(
        self,
        fn: Callable | None = None,
        *,
        status_code: int = None,
        process_response: bool = True,
        order: int = -1,
    ):
        """Flask-style hook: ``(response) -> Response``.

        Use as ``@app.after_request`` or ``@app.after_request()``.
        Returning ``None`` keeps the previous response.
        """
        if status_code is not None or process_response is not True:
            warn_deprecated(
                'after_request(status_code=..., process_response=...)',
                alternative='mutate and return the Response from the hook',
                removal='2.0',
            )

        def register(middleware: Callable[..., Any]):
            self.add_after_request(
                middleware,
                status_code=status_code,
                process_response=process_response,
                order=order,
            )
            return middleware

        if fn is not None and callable(fn):
            return register(fn)
        return register

    def add_before_request(
        self,
        middleware: Callable[..., Any],
        *,
        status_code: int = 200,
        process_response: bool = True,
        order: int = -1,
    ):
        """Register a before_request hook (Flask-style ``add_before_request``)."""
        entry = self.set_middleware(
            status_code=status_code,
            middleware=middleware,
            order=order,
            process_response=process_response,
        )
        if order < 0 or order >= len(self.__before_request):
            self.__before_request.append(entry)
        else:
            self.__before_request.insert(order, entry)
        return middleware

    def add_after_request(
        self,
        middleware: Callable[..., Any],
        *,
        status_code: int = None,
        process_response: bool = True,
        order: int = -1,
    ):
        """Register an after_request hook (Flask-style ``add_after_request``)."""
        entry = self.set_middleware(
            status_code=status_code,
            middleware=middleware,
            order=order,
            process_response=process_response,
        )
        if order < 0 or order >= len(self.__after_request):
            self.__after_request.append(entry)
        else:
            self.__after_request.insert(order, entry)
        return middleware

    # Docs / older aliases
    def add_before_request_middleware(self, middleware: Callable[..., Any], **kwargs):
        warn_deprecated(
            'add_before_request_middleware',
            alternative='add_before_request',
            removal='2.0',
        )
        return self.add_before_request(middleware, **kwargs)

    def add_after_request_middleware(self, middleware: Callable[..., Any], **kwargs):
        warn_deprecated(
            'add_after_request_middleware',
            alternative='add_after_request',
            removal='2.0',
        )
        return self.add_after_request(middleware, **kwargs)

    def middleware(self, order: int = -1):
        """Register onion middleware: ``async def mw(request, call_next)``."""
        def wrapper(middleware: Callable[..., Any]):
            entry = self._set_onion_middleware(middleware=middleware, order=order)
            if order < 0 or order >= len(self.__onion):
                self.__onion.append(entry)
            else:
                self.__onion.insert(order, entry)
            return middleware
        return wrapper

    def clear_before_request_middleware(self):
        self.__before_request.clear()

    def remove_before_middleware(self, index: int = -1):
        return self.__before_request.pop(index)

    def remove_after_middleware(self, index: int = -1):
        return self.__after_request.pop(index)

    def clear_after_request_middleware(self):
        self.__after_request.clear()

    def clear_onion_middlewares(self):
        self.__onion.clear()

    async def process_middleware(
        self,
        resp: Union[Request, Response, str],
        middlewares: list[dict[str, Union[int, Callable, bool]]]
    ):
        response, status_code, process_response = None, 200, True

        for middle_dict in middlewares:
            status_code, middle, _, process_response = middle_dict.values()

            variables = RouteManager.inspect_function(callback=middle)
            var = []

            for vars in variables:
                for k in vars.keys():
                    var.append(k)

            kwargs = {key: resp for key in var}
            kwargs = RouteManager.validate_callable_args(middle, **kwargs)

            if inspect.iscoroutinefunction(middle):
                response = await middle(**kwargs)
            else:
                response = middle(**kwargs)

            if response:
                break

        if not isinstance(resp, Response) and response:
            # Prefer Response.status_code; otherwise decorator status_code (Flask-compat)
            resolved_status = status_code if status_code is not None else 200
            if isinstance(response, Response):
                resolved_status = response.status_code
            elif isinstance(response, Template) and (status_code is None or status_code == 200):
                tmpl_code = getattr(response, 'status_code', None) or getattr(response, 'code', None)
                if tmpl_code:
                    resolved_status = tmpl_code

            return MiddlewareResult(
                status_code=resolved_status,
                process_response=process_response if process_response is not None else True,
                content=response
            )

        if isinstance(resp, Response):
            # after_request: None keeps previous response (tolerant)
            if response is not None and not isinstance(response, Response):
                raise TypeError(
                    f'All after request middleware need return Response instances, '
                    f'but got {type(response).__name__}'
                )

            return MiddlewareResult(
                content=response if isinstance(response, Response) else resp,
                status_code=resp.status_code,
                process_response=None
            )

        return None

    async def run_onion(
        self,
        request: Request,
        call_handler: Callable[[], Any],
    ) -> Response | MiddlewareResult | Any:
        """Run onion middlewares then ``call_handler`` (returns Response or raw result)."""
        chain = list(self.__onion)

        async def _terminal():
            return await call_handler() if inspect.iscoroutinefunction(call_handler) else call_handler()

        async def build(index: int):
            if index >= len(chain):
                return await _terminal()

            mw = chain[index]['middleware']

            async def call_next():
                return await build(index + 1)

            if inspect.iscoroutinefunction(mw):
                return await mw(request, call_next)
            return mw(request, call_next)

        return await build(0)

    def _set_onion_middleware(self, middleware: Callable, order: int = -1):
        if not callable(middleware):
            raise TypeError('The middleware must be a callable function')

        sig = inspect.signature(middleware)
        params = list(sig.parameters.values())
        if len(params) < 2:
            raise TypeError(
                f"The {middleware.__name__}'s onion middleware must receive "
                f"(request, call_next)"
            )
        return {'middleware': middleware, 'order': order, 'style': 'onion'}

    def set_middleware(self, status_code: int, middleware: Callable, process_response: bool = True, order: int = -1):
        if not isinstance(order, int):
            raise ValueError(f'middleware order must be an integer instances, but got {type(order).__name__}')

        if status_code and status_code not in HTTPStatusCode.code_list():
            raise ValueError('HttpStatusCode is not valid')

        if not callable(middleware):
            raise TypeError('The middleware must be a callable function')

        sig = inspect.signature(middleware)
        params = list(sig.parameters.values())

        if len(params) >= 2:
            raise TypeError(
                f"Use @app.middleware for onion-style (request, call_next) handlers; "
                f"{middleware.__name__} has {len(params)} parameters"
            )

        if params and not all(
            param.annotation in [Request, Response, inspect.Parameter.empty]
            for param in params
        ):
            annotations = [p.annotation for p in params if p.annotation not in (inspect.Parameter.empty,)]
            if annotations and not all(a in [Request, Response] for a in annotations):
                raise TypeError(
                    f"All parameters of {middleware.__name__}'s middleware must be a Request or Response instances"
                )

        return {'status_code': status_code, 'middleware': middleware, 'order': order, 'process_response': process_response}

    def __repr__(self):
        return (
            f'MiddlewareManager('
            f'before_request_middlewares={len(self.__before_request)}, '
            f'after_request_middlewares={len(self.__after_request)}, '
            f'onion_middlewares={len(self.__onion)})'
        )
