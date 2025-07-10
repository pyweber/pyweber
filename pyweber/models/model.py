from typing import Callable, Any
import inspect

class BaseField:
    def __init__(self, **kwargs):
        self.__fields__ = self.__class__.__annotations__

        for field, _ in self.__fields__.items():
            if field in kwargs:
                value = kwargs[value]
            elif hasattr(self.__class__, field):
                value = getattr(self.__class__, field)
            else:
                raise ValueError(f'{field} is a mandatory field')
            
            setattr(self, field, value)
    
    def validator(self, callback: Callable[..., Any]):
        assert callable(callback)
