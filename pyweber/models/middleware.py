from typing import Callable, Union
import inspect
from pyweber.models.request import Request
from pyweber.models.response import Response
from pyweber.core.element import Element
from pyweber.core.template import Template
from pyweber.utils.types import HTTPStatusCode
from pyweber.models.routes import RouteManager

class MiddlewareManager:
    def __init__(self):
        self.__before_request: list[dict[str, Union[int, Callable]]] = []
        self.__after_request: list[dict[str, Union[int, Callable]]] = []
    
    @property
    def get_before_request_middlewares(self):
        return self.__before_request
    
    @property
    def get_after_request_middlewares(self):
        return self.__after_request
    
    def before_request(self, status_code: int = 200, order: int = -1):
        def wrapper(middleware: Callable[..., Template | Element | str | None]):
            self.__before_request.insert(order, self.set_middleware(status_code=status_code, middleware=middleware, order=order))
            return middleware
        return wrapper
    
    def after_request(self, status_code: int = None, order: int = -1):
        def wrapper(middleware: Callable[..., Response | None]):
            self.__after_request.insert(order, self.set_middleware(status_code=status_code, middleware=middleware, order=order))
            return middleware
        return wrapper
    
    def clear_before_request_middleware(self):
        self.__before_request.clear()
    
    def clear_after_request_middleware(self):
        self.__after_request.clear()
    
    async def process_middleware(self, resp: Union[Request, Response, str], middlewares: list[dict[str, Union[int, Callable]]]) -> None | tuple[int, Response | Template | Element | str | dict]:
        for middle_dict in middlewares:
            status_code, middle, _ = middle_dict.values()

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
                return status_code, response
    
    def set_middleware(self, status_code: int, middleware: Callable, order: int = -1):
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
            raise TypeError(f"All parameters of {middleware.__name__}'s middleware must be a Request or Response instances, but got ")
        
        return {'status_code': status_code, 'middleware': middleware, 'order': order}
    
    def __repr__(self):
        return (
            f'MiddlewareManager('
            f'before_request_middlewares={len(self.__before_request)}, '
            f'after_request_middlewares={len(self.__after_request)})'
        )