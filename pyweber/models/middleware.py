from typing import Callable, Union
from dataclasses import dataclass
import inspect
from pyweber.models.request import Request
from pyweber.models.response import Response
from pyweber.core.element import Element
from pyweber.core.template import Template
from pyweber.utils.types import HTTPStatusCode
from pyweber.models.routes import RouteManager

@dataclass
class MiddlewareResult: # pragma: no cover
    status_code: int
    process_response: bool
    content: Union[Template, Element, Response, dict, str]

class MiddlewareManager: # pragma: no cover
    def __init__(self):
        self.__before_request: list[dict[str, Union[int, Callable, bool]]] = []
        self.__after_request: list[dict[str, Union[int, Callable, bool]]] = []
    
    @property
    def get_before_request_middlewares(self):
        return self.__before_request
    
    @property
    def get_after_request_middlewares(self):
        return self.__after_request
    
    def before_request(self, status_code: int = 200, process_response: bool = True, order: int = -1):
        def wrapper(middleware: Callable[..., Template | Element | str | None]):
            self.__before_request.insert(order, self.set_middleware(
                    status_code=status_code,
                    middleware=middleware,
                    order=order,
                    process_response=process_response
                )
            )
            return middleware
        return wrapper
    
    def after_request(self, status_code: int = None, process_response: bool = True, order: int = -1):
        def wrapper(middleware: Callable[..., Response | None]):
            self.__after_request.insert(order, self.set_middleware(
                    status_code=status_code,
                    middleware=middleware,
                    order=order,
                    process_response=process_response
                )
            )
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
    
    async def process_middleware(
        self,
        resp: Union[Request, Response, str],
        middlewares: list[dict[str, Union[int, Callable, bool]]]
    ):
        response, status_code, process_response = None, None, None

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
            return MiddlewareResult(
                status_code=status_code,
                process_response=process_response,
                content=response
            )
        
        if isinstance(resp, Response):
            if middlewares and not isinstance(response, Response):
                raise TypeError(f'All after request middleware need return Response instances, but got {type(response).__name__}')
            
            return MiddlewareResult(
                content=response or resp,
                status_code=resp.status_code,
                process_response=None
            )
    
    def set_middleware(self, status_code: int, middleware: Callable, process_response: bool = True, order: int = -1):
        if not isinstance(order, int):
            raise ValueError(f'middleware order must be an integer instances, but got {type(order).__name__}')
        
        if status_code and status_code not in HTTPStatusCode.code_list():
            raise ValueError('HttpStatusCode is not valid')
        
        if not callable(middleware):
            raise TypeError('The middleware must be a callable function')
        
        sig = inspect.signature(middleware)
        params = list(sig.parameters.values())

        if len(params) > 1:
            raise TypeError(f"The {middleware.__name__}'s middleware must be receive one parameter only")
        
        if params and not all(param.annotation in [Request, Response] for param in params if param):
            raise TypeError(f"All parameters of {middleware.__name__}'s middleware must be a Request or Response instances")
        
        return {'status_code': status_code, 'middleware': middleware, 'order': order, 'process_response': process_response}
    
    def __repr__(self):
        return (
            f'MiddlewareManager('
            f'before_request_middlewares={len(self.__before_request)}, '
            f'after_request_middlewares={len(self.__after_request)})'
        )