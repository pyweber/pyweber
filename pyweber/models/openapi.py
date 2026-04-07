import re
import inspect
from typing import Any, Callable
import dataclasses
import sys

from pyweber.utils.types import ContentTypes

class OpenApiProcessor:
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
    def mapping_swagger_types():
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
    def default_format_type(type: str):
        return {'string': None, 'integer': 'int32', 'float': 'float', 'boolean': 'boolean'}.get(type, None)

    @staticmethod
    def get_swagger_type(py_type: type, format_type: str = None):
        mapping_types = OpenApiProcessor.mapping_swagger_types()
        swagger_type = mapping_types.get(py_type.__name__, mapping_types['str'])
        return {'type': {'type': swagger_type['type'], 'format': format_type if format_type in swagger_type['formats'] else None}}

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

        if annotation.__name__ in ['File', 'bytes', 'bytearray']:
            return 'file'

        if annotation.__name__ == 'Request':
            return 'request'

        if hasattr(annotation, '__init__') and annotation.__init__ != object.__init__:
            return 'normal_class'

        return 'empty_class'

    @classmethod
    def get_type_parameter(cls, parameter: inspect.Parameter):
        if parameter.annotation == inspect._empty:
            return cls.get_swagger_type(str)

        if parameter.annotation.__name__ in cls.mapping_swagger_types():
            return cls.get_swagger_type(parameter.annotation)

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

        r, _, q = route.partition('?')
        path_params = set(cls.get_route_parameters(r))
        query_params = set(cls.get_route_parameters(q))

        for parameter in path_params | query_params:
            location = 'path' if parameter in path_params else 'query'
            if parameter in parameter_details:
                param_type = cls.get_type_parameter(parameter_details[parameter])['type']

                route_parameters[parameter] = {
                    'name': parameter,
                    'in': location,
                    'schema': {
                        'type': param_type['type'],
                        'format': param_type['format']
                    },
                    'example': cls.get_format_example(
                        param_type['format'] or cls.default_format_type(param_type['type'])
                    )
                }

                if parameter_details.get(parameter).default == inspect._empty:
                    route_parameters[parameter]['required'] = True
                else:
                    route_parameters[parameter]['default'] = parameter_details.get(parameter).default

            else:
                route_parameters[parameter] = {
                    'name': parameter,
                    'in': location,
                    'required': True,
                    'schema': {
                        'type': 'string',
                        'format': None
                    },
                    'example': cls.get_format_example('string')
                }

        return route_parameters

    @classmethod
    def get_body_spec(cls, route: str, callback: Callable):
        assert isinstance(route, str) and callable(callback)
        request_body = {'description': 'Pyweber Request Body', 'required': True, 'content': {}}

        master_props = {}
        master_required = []
        has_binary = False

        for title, parameter in cls.get_callback_parameters(callback=callback).items():
            if title not in cls.get_route_parameters(route=route):

                annotation = parameter.annotation
                parameter_solved = cls.resolve_class_type(parameter=parameter)

                if parameter_solved == 'file':
                    master_props[parameter.name] = {
                        'title': parameter.name.capitalize(),
                        'type': 'string',
                        'format': 'binary'
                    }
                    master_required.append(parameter.name)
                    has_binary = True
                elif parameter_solved == 'request':
                    pass

                elif parameter_solved == 'pydantic':
                    pydantic_scheme = annotation.model_json_schema()
                    master_props = {**master_props, **pydantic_scheme['properties']}
                    master_required.extend(pydantic_scheme['required'])

                elif parameter_solved == 'dataclass':
                    properities = {}
                    required = []


                    if sys.version_info >= (3, 14):
                        import annotationlib
                        field_annotations = annotationlib.get_annotations(annotation)

                        for name, field_type in field_annotations.items():
                            properities[name] = {
                                'title': name.capitalize(),
                                'type': cls.get_swagger_type(field_type)['type']['type'],
                            }

                            if name in annotation.__dict__.keys():
                                properities[name]['default'] = annotation.__dict__.get(name)
                                continue

                            required.append(name)
                    else:
                        field_annotations = getattr(annotation, '__dataclass_fields__', {})

                        for p in field_annotations.values():
                            properities[p.name] = {
                                'title': str(p.name).capitalize(),
                                'type': cls.get_swagger_type(p.type)['type']['type'],
                            }

                            if not isinstance(p.default, dataclasses._MISSING_TYPE):
                                properities[p.name]['default'] = p.default
                                continue

                            required.append(p.name)

                    master_props = {**master_props, **properities}
                    master_required.extend(required)
                elif parameter_solved == 'normal_class':
                    if annotation.__name__ not in cls.mapping_swagger_types():
                        properities = {}
                        required = []

                        parameters = inspect.signature(annotation.__init__).parameters
                        for p, t in parameters.items():
                            if p.lower() not in ['self', 'cls']:
                                properities[p] = {
                                    'title': str(p).capitalize(),
                                    'type': cls.get_swagger_type(t.annotation)['type']['type']
                                }

                                if t.default != inspect._empty:
                                    properities[p]['default'] = t.default
                                    continue

                                required.append(p)

                        master_props = {**master_props, **properities}
                        master_required.extend(required)

                else:
                    if annotation.__name__ not in cls.mapping_swagger_types():
                        properities = {}
                        required = []

                        if sys.version_info >= (3, 14):
                            import annotationlib
                            annotations = annotationlib.get_annotations(annotation)
                        else:
                            annotations = annotation.__dict__.get('__annotations__', {})

                        for p, t in annotations.items():
                            properities[p] = {
                                'title': str(p).capitalize(),
                                'type': cls.get_swagger_type(t)['type']['type']
                            }

                            if p in annotation.__dict__:
                                properities[p]['default'] = annotation.__dict__.get(p)
                                continue

                            required.append(p)

                        master_props = {**master_props, **properities}
                        master_required.extend(required)

                    else:
                        sw_type = cls.get_swagger_type(parameter.annotation)
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

            schema = {
                'schema': {
                    'properties': master_props,
                    'required': list(set(master_required)),
                    'title': callback.__name__.capitalize(),
                    'type': 'object'
                }
            }

            if has_binary:
                request_body['content'][ContentTypes.form_data.value] = schema
                request_body['content'][ContentTypes.unkown.value] = schema

            else:
                request_body['content'][ContentTypes.json.value] = schema
                request_body['content'][ContentTypes.form_encode.value] = schema
                request_body['content'][ContentTypes.unkown.value] = schema
                request_body['content'][ContentTypes.txt.value] = schema

        return request_body

    @classmethod
    def prepare_callback_kwargs(cls, callback: Callable, **kwargs):
        assert callable(callback)

        all_callback_parameters = cls.get_callback_parameters(callback)
        kwd: dict[str, Any] = {}

        for name, parameter in all_callback_parameters.items():
            class_resolved = cls.resolve_class_type(parameter)
            annotation = parameter.annotation

            if class_resolved == 'file':
                if name in kwargs:
                    kwd[name] = kwargs.pop(name)[0]

            elif class_resolved in ['pydantic', 'dataclass', 'normal_class']:
                parameters = {}

                for key in cls.get_callback_parameters(annotation).keys():
                    parameters[key] = kwargs.pop(key)

                kwd[name] = annotation(**parameters)

            elif class_resolved == 'request':
                kwd[name] = kwargs.pop('request')

            else:
                if annotation.__name__ not in cls.mapping_swagger_types() and annotation != inspect._empty:

                    if sys.version_info < (3, 14):
                        instance = annotation()
                        for key in instance.__annotations__.keys():
                            setattr(instance, key, kwargs.pop(key))
                    else:
                        import annotationlib
                        instance=annotation
                        for key in annotationlib.get_annotations(instance).keys():
                            setattr(instance, key, kwargs.pop(key))

                    kwd[name] = instance

                else:
                    if parameter.kind not in [inspect.Parameter.VAR_KEYWORD, inspect.Parameter.VAR_POSITIONAL]:
                        kwd[name] = kwargs.pop(name)

        if kwargs:
            has_var_keyword = any(
                p.kind == inspect.Parameter.VAR_KEYWORD
                for p in all_callback_parameters.values()
            )

            has_var_positional = any(
                p.kind == inspect.Parameter.VAR_POSITIONAL
                for p in all_callback_parameters.values()
            )

            if has_var_keyword:
                var_kw_name = next(
                    name for name, p in all_callback_parameters.items()
                    if p.kind == inspect.Parameter.VAR_KEYWORD
                )
                kwd[var_kw_name] = kwargs

            elif has_var_positional:
                var_pos_name = next(
                    name for name, p in all_callback_parameters.items()
                    if p.kind == inspect.Parameter.VAR_POSITIONAL
                )
                kwd[var_pos_name] = list(kwargs.values())

        return kwd
