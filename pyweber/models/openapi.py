import re
import inspect
from typing import Any, Callable
import dataclasses

from pyweber.utils.types import ContentTypes

class OpenApiProcessor: # pragma: no cover
    @staticmethod
    def get_format_example(format_type: str):
        examples = {
            'date': '2023-12-25',
            'date-time': '2023-12-25T14:30:00Z',
            'password': 'mySecretPassword123',
            'byte': 'U3dhZ2dlciByb2Nrcw==',
            'binary': 'binary_data_here',
            'email': 'user@example.com',
            'uuid': '550e8400-e29b-41d4-a716-446655440000',
            'uri': 'https://pyweber.dev/en/latest/installation/',
            'hostname': 'docs.pyweber.dev',
            'ipv4': '127.0.0.1',
            'ipv6': '2001:0db8:85a3:0000:0000:8a2e:0370:7334',
            'int32': 2147483647,
            'int64': 9223372036854775807,
            'float': 3.14159,
            'double': 3.141592653589793,
            'array': [1,2,3],
            'bool': True
        }

        return examples.get(format_type, 'pyweber')
    
    @staticmethod
    def mapping_swegger_types():
        return {
            "str": {'type': 'string', 'formats': ['date', 'date-time', 'password', 'byte', 'binary', 'email', 'uuid', 'uri', 'hostname', 'ipv4', 'ipv6']},
            "int": {'type': 'integer', 'formats': ['int32', 'int64']},
            "float": {'type': 'number', 'formats': ['float', 'double']},
            "list": {'type': 'array', 'formats': []},
            "set": {'type': 'array', 'formats': []},
            "tuple": {'type': 'array', 'formats': []},
            'dict': {'type': 'object', 'formats': []},
            'bool': {'type': 'boolean', 'formats': []}
        }
    
    @staticmethod
    def default_format_types(type: str):
        return {'string': None, 'integer': 'int32', 'float': 'float', 'boolean': 'boolean'}.get(type, None)
    
    @staticmethod
    def get_swegger_types(py_type: type, format_type: str = None):
        mapping_types = OpenApiProcessor.mapping_swegger_types()
        swegger_type = mapping_types.get(py_type.__name__, mapping_types['str'])
        return {'type': {'type': swegger_type['type'], 'format': format_type if format_type in swegger_type else None}}
    
    @staticmethod
    def is_valid_route_param_type(py_type: str):
        return py_type in ['str', 'int', 'float', 'bool']
    
    @classmethod
    def resolve_class_type(cls, parameter: inspect.Parameter):
        assert isinstance(parameter, inspect.Parameter)
        annotation = parameter.annotation

        if hasattr(annotation, '__pydantic_validator__'):
            return 'pydantic'
        
        if hasattr(annotation, '__dataclass_fields__'):
            return 'dataclass'
        
        if hasattr(annotation, '__init__') and annotation.__init__ != object.__init__:
            return 'normal_class'
        
        return 'empty_class'
    
    @classmethod
    def get_type_parameter(cls, parameter: inspect.Parameter):
        if parameter.annotation == inspect._empty:
            return cls.get_swegger_types(str)
        
        if parameter.annotation.__name__ in cls.mapping_swegger_types():
            return cls.get_swegger_types(parameter.annotation)
        
    @classmethod
    def get_route_parameters(cls, route: str) -> list[str]:
        assert isinstance(route, str)
        return re.findall(r"{\s*(.*?)\s*}", route)
    
    @classmethod
    def get_callback_parameters(cls, callback: Callable):
        assert callable(callback)
        return {param.name: param for param in inspect.signature(callback).parameters.values()}
    
    @classmethod
    def get_route_spec(cls, route: str, callback: Callable):
        assert isinstance(route, str) and callable(callback)

        parameter_details = cls.get_callback_parameters(callback)
        route_parameters: dict[str, dict[str, Any]] = {}

        for parameter in cls.get_route_parameters(route=route):
            if parameter in parameter_details:
                param_type = cls.get_type_parameter(parameter_details[parameter])['type']

                route_parameters[parameter] = {
                    'name': parameter,
                    'in': 'path',
                    'schema': {
                        'type': param_type['type'],
                        'format': param_type['format']
                    },
                    'example': cls.get_format_example(
                        param_type['format'] or cls.default_format_types(param_type['type'])
                    )
                }

                if parameter_details.get(parameter).default == inspect._empty:
                    route_parameters[parameter]['required'] = True
                else:
                    route_parameters[parameter]['default'] = parameter_details.get(parameter).default

            else:
                route_parameters[parameter] = {
                    'name': parameter,
                    'in': 'path',
                    'required': True,
                    'schema': {
                        'type': 'string',
                        'format': None
                    },
                    'example': cls.get_format_example(
                        param_type['format'] or cls.default_format_types(param_type['type'])
                    )
                }
        
        return route_parameters
    
    @classmethod
    def get_body_spec(cls, route: str, callback: Callable):
        assert isinstance(route, str) and callable(callback)
        request_body = {'description': 'Pyweber Request Body', 'required': True, 'content': {}}

        master_props = {}
        master_required = []

        for title, parameter in cls.get_callback_parameters(callback=callback).items():
            if title not in cls.get_route_parameters(route=route):

                annotation = parameter.annotation
                parameter_solved = cls.resolve_class_type(parameter=parameter)

                if parameter_solved == 'pydantic':
                    pydantic_scheme = annotation.model_json_schema()
                    master_props = {**master_props, **pydantic_scheme['properties']}
                    master_required.extend(pydantic_scheme['required'])

                elif parameter_solved == 'dataclass':
                    properities = {}
                    required = []
                    for p in getattr(annotation, '__dataclass_fields__', {}).values():
                        properities[p.name] = {
                            'title': str(p.name).capitalize(),
                            'type': cls.get_swegger_types(p.type)['type']['type']
                        }

                        if not isinstance(p.default, dataclasses._MISSING_TYPE):
                            properities[p.name]['default'] = p.default
                            continue

                        required.append(p.name)
                    
                    master_props = {**master_props, **properities}
                    master_required.extend(required)
                
                else:
                    if annotation.__name__ not in cls.mapping_swegger_types():
                        properities = {}
                        required = []
                        for p, t in annotation.__dict__.get('__annotations__', {}).items():
                            properities[p] = {
                                'title': str(p).capitalize(),
                                'type': cls.get_swegger_types(t)['type']['type']
                            }

                            if p in annotation.__dict__:
                                properities[p]['default'] = annotation.__dict__.get(p)
                                continue

                            required.append(p)
                        
                        master_props = {**master_props, **properities}
                        master_required.extend(required)

                    else:
                        sw_type = cls.get_swegger_types(parameter.annotation)
                        properities = {
                            title: {
                                'title': title.capitalize(),
                                'type': sw_type['type']['type']
                            }
                        }

                        if parameter.default != inspect._empty:
                            properities[title]['default'] = parameter.default
                        else:
                            master_required.append(title)
                        
                        master_props = {**master_props, **properities}

        if len(master_props.keys()) > 0:
            request_body['content'][ContentTypes.json.value] = {
                'schema': {
                    'properties': master_props,
                    'required': list(set(master_required)),
                    'title': callback.__name__.capitalize(),
                    'type': 'object'
                }
            }
        
        return request_body
    
    @classmethod
    def prepare_callback_kwargs(cls, callback: Callable, **kwargs):
        assert callable(callback)

        all_callback_parameters = cls.get_callback_parameters(callback)
        kwd: dict[str, Any] = {}

        for name, parameter in all_callback_parameters.items():
            class_resolved = cls.resolve_class_type(parameter)
            annotation = parameter.annotation

            if class_resolved in ['pydantic', 'dataclass', 'normal_class']:
                parameters = {}

                for key in cls.get_callback_parameters(annotation).keys():
                    parameters[key] = kwargs.pop(key)
                
                kwd[name] = annotation(**parameters)

            else:
                
                if annotation.__name__ not in cls.mapping_swegger_types() and annotation != inspect._empty:
                    instance = annotation()
                    for key in instance.__annotations__.keys():
                        setattr(instance, key, kwargs.pop(key))

                    kwd[name] = instance

                else:
                    if parameter.kind not in [inspect.Parameter.VAR_KEYWORD, inspect.Parameter.VAR_POSITIONAL]:
                        kwd[name] = kwargs.pop(name)
        
        if kwargs:
            kwd['kwargs'] = kwargs
        
        return kwd