import re
import inspect
import types
from typing import Any, Callable, Union, get_args, get_origin
import dataclasses
import sys

from pyweber.utils.types import ContentTypes, HTTPStatusCode
from pyweber.models.security import (
    APIKeyCookie,
    APIKeyHeader,
    APIKeyQuery,
    HTTPBasic,
    HTTPBearer,
    SecurityScheme,
    normalize_security_requirements,
)

# Builtin / common names that AI-generated and postponed annotations often use as strings.
_PRIMITIVE_TYPE_MAP: dict[str, type] = {
    'str': str,
    'int': int,
    'float': float,
    'bool': bool,
    'list': list,
    'dict': dict,
    'set': set,
    'tuple': tuple,
    'bytes': bytes,
    'bytearray': bytearray,
    'None': type(None),
}


def _is_union_origin(origin: Any) -> bool:
    """True for typing.Union and PEP 604 ``X | Y`` (types.UnionType on 3.10+)."""
    if origin is Union:
        return True
    union_type = getattr(types, 'UnionType', None)
    return union_type is not None and origin is union_type


@dataclasses.dataclass
class OpenAPIConfig:
    """App-level OpenAPI / Swagger configuration."""

    title: str = 'Pyweber Documentation'
    version: str = '1.0.0'
    description: str | None = None
    contact: dict[str, str] | None = None
    license: dict[str, str] | None = None
    servers: list[dict[str, str]] | None = None
    docs_url: str | None = '/docs'
    openapi_url: str | None = '/openapi.json'
    security_schemes: dict[str, SecurityScheme] | None = None
    security: list[str] | list[dict[str, list[str]]] | None = None
    tags: list[dict[str, str]] | None = None
    expose_in_production: bool = False

    def normalized_security(self) -> list[dict[str, list[str]]] | None:
        return normalize_security_requirements(self.security)

    def security_schemes_openapi(self) -> dict[str, dict[str, Any]]:
        schemes = self.security_schemes or {}
        return {name: scheme.to_openapi() for name, scheme in schemes.items()}


class SchemaRegistry:
    """Collect named schemas for components.schemas and emit $ref pointers."""

    def __init__(self):
        self.schemas: dict[str, dict[str, Any]] = {}

    def register(self, name: str, schema: dict[str, Any]) -> dict[str, Any]:
        safe = re.sub(r'[^A-Za-z0-9_.-]', '_', name) or 'Schema'
        base = safe
        idx = 1
        while safe in self.schemas and self.schemas[safe] != schema:
            safe = f'{base}_{idx}'
            idx += 1
        self.schemas[safe] = schema
        return {'$ref': f'#/components/schemas/{safe}'}

    def add_from_pydantic(self, model: type) -> dict[str, Any]:
        raw = model.model_json_schema()
        defs = raw.pop('$defs', None) or raw.pop('definitions', None) or {}
        for def_name, def_schema in defs.items():
            self.schemas[def_name] = self._rewrite_refs(def_schema)
        name = getattr(model, '__name__', 'Model')
        return self.register(name, self._rewrite_refs(raw))

    @staticmethod
    def _rewrite_refs(node: Any) -> Any:
        if isinstance(node, dict):
            if '$ref' in node and isinstance(node['$ref'], str):
                ref = node['$ref']
                if ref.startswith('#/$defs/'):
                    node = {**node, '$ref': '#/components/schemas/' + ref.split('/')[-1]}
                elif ref.startswith('#/definitions/'):
                    node = {**node, '$ref': '#/components/schemas/' + ref.split('/')[-1]}
            return {k: SchemaRegistry._rewrite_refs(v) for k, v in node.items()}
        if isinstance(node, list):
            return [SchemaRegistry._rewrite_refs(v) for v in node]
        return node


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

    @classmethod
    def normalize_annotation(cls, annotation: Any) -> Any:
        """Resolve string/forward annotations to real types when possible.

        Handles common AI / ``from __future__ import annotations`` cases like
        ``"str"``, ``"int | None"``, ``"Optional[str]"``, ``"list[str]"``.
        """
        if annotation is inspect.Parameter.empty or annotation is inspect._empty:
            return inspect._empty

        if annotation is None:
            return type(None)

        # typing.ForwardRef
        forward_arg = getattr(annotation, '__forward_arg__', None)
        if isinstance(forward_arg, str):
            return cls.normalize_annotation(forward_arg)

        if isinstance(annotation, str):
            return cls._resolve_string_annotation(annotation)

        return annotation

    @classmethod
    def _resolve_string_annotation(cls, text: str) -> Any:
        text = text.strip().strip('\'"')
        if not text:
            return str

        # X | Y | None  (PEP 604)
        if '|' in text:
            parts = [p.strip() for p in text.split('|')]
            non_none = [p for p in parts if p not in ('None', 'NoneType')]
            target = non_none[0] if non_none else 'str'
            return cls._resolve_string_annotation(target)

        # Optional[X], Union[X, Y], list[X], dict[K, V], ...
        if '[' in text and text.endswith(']'):
            base, _, inner = text.partition('[')
            base = base.strip()
            inner = inner[:-1].strip()

            if base in ('Optional', 'Union'):
                first = inner.split(',')[0].strip()
                return cls._resolve_string_annotation(first)

            if base in ('Literal',):
                return str

            if base in _PRIMITIVE_TYPE_MAP:
                return _PRIMITIVE_TYPE_MAP[base]

            return str

        if text in _PRIMITIVE_TYPE_MAP:
            return _PRIMITIVE_TYPE_MAP[text]

        # Unknown class name as a bare string — safer as str for OpenAPI than crashing.
        return str

    @classmethod
    def annotation_type_name(cls, annotation: Any) -> str:
        annotation = cls.normalize_annotation(annotation)
        if annotation is inspect._empty:
            return 'str'

        if isinstance(annotation, type):
            return annotation.__name__

        origin = get_origin(annotation)
        if origin is not None:
            # Union / Optional / PEP 604 (int | None) → prefer first non-None arg's name
            if _is_union_origin(origin):
                args = [a for a in get_args(annotation) if a is not type(None)]
                if args:
                    return cls.annotation_type_name(args[0])
            name = getattr(origin, '__name__', None)
            if name:
                return name

        return 'str'

    @classmethod
    def get_swagger_type(cls, py_type: Any, format_type: str = None):
        mapping_types = OpenApiProcessor.mapping_swagger_types()
        name = cls.annotation_type_name(py_type)
        swagger_type = mapping_types.get(name, mapping_types['str'])
        return {
            'type': {
                'type': swagger_type['type'],
                'format': format_type if format_type in swagger_type['formats'] else None,
            }
        }

    @staticmethod
    def is_valid_route_param_type(py_type: str):
        return py_type in ['str', 'int', 'float', 'bool']

    @classmethod
    def coerce_value(cls, name: str, value: Any, annotation: Any) -> Any:
        """Coerce a route/query string value to the annotated primitive type."""
        from pyweber.utils.exceptions import ParameterConversionError

        annotation = cls.normalize_annotation(annotation)
        if annotation is inspect._empty or value is None:
            return value

        # Already correct type
        if annotation in (str, int, float, bool) and isinstance(value, annotation):
            return value

        type_name = cls.annotation_type_name(annotation)
        raw = value if not isinstance(value, str) else value

        try:
            if annotation is bool or type_name == 'bool':
                if isinstance(value, bool):
                    return value
                text = str(value).strip().lower()
                if text in {'1', 'true', 'yes', 'on'}:
                    return True
                if text in {'0', 'false', 'no', 'off'}:
                    return False
                raise ValueError(f'invalid boolean {value!r}')

            if annotation is int or type_name == 'int':
                return int(value)

            if annotation is float or type_name == 'float':
                return float(value)

            if annotation is str or type_name == 'str':
                return str(value)

            # Marker format classes (EmailFormat, etc.) — keep as str
            if isinstance(annotation, type) and annotation.__name__.endswith('Format'):
                return str(value)

            return value
        except (TypeError, ValueError) as exc:
            raise ParameterConversionError(name, raw, type_name or str(annotation), cause=exc) from exc

    @classmethod
    def resolve_class_type(cls, parameter: inspect.Parameter):
        assert isinstance(parameter, inspect.Parameter)
        annotation = cls.normalize_annotation(parameter.annotation)

        if annotation is inspect._empty:
            return 'primitive'

        type_name = cls.annotation_type_name(annotation)
        if type_name in cls.mapping_swagger_types():
            return 'primitive'

        if hasattr(annotation, '__pydantic_validator__'):
            return 'pydantic'

        if hasattr(annotation, '__dataclass_fields__'):
            return 'dataclass'

        if type_name in ['File', 'bytes', 'bytearray']:
            return 'file'

        if type_name == 'Request':
            return 'request'

        if isinstance(annotation, type) and hasattr(annotation, '__init__') and annotation.__init__ != object.__init__:
            return 'normal_class'

        return 'empty_class'

    @classmethod
    def get_type_parameter(cls, parameter: inspect.Parameter):
        annotation = cls.normalize_annotation(parameter.annotation)
        if annotation is inspect._empty:
            return cls.get_swagger_type(str)

        return cls.get_swagger_type(annotation)

    @classmethod
    def get_route_parameters(cls, route: str) -> list[str]:
        assert isinstance(route, str)
        return re.findall(r"{\s*(.*?)\s*}", route)

    @classmethod
    def get_callback_parameters(cls, callback: Callable):
        assert callable(callback)
        try:
            from typing import get_type_hints
            hints = get_type_hints(callback, include_extras=True)
        except Exception:
            hints = {}

        params: dict[str, inspect.Parameter] = {}
        for name, param in inspect.signature(callback).parameters.items():
            annotation = hints.get(name, param.annotation)
            annotation = cls.normalize_annotation(annotation)
            params[name] = param.replace(annotation=annotation)
        return params

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
    def _swagger_type_name_from_annotation(cls, annotation: Any) -> str:
        return cls.get_swagger_type(annotation)['type']['type']

    @classmethod
    def get_body_spec(cls, route: str, callback: Callable):
        assert isinstance(route, str) and callable(callback)
        request_body = {'description': 'Pyweber Request Body', 'required': True, 'content': {}}

        master_props = {}
        master_required = []
        has_binary = False

        for title, parameter in cls.get_callback_parameters(callback=callback).items():
            if title not in cls.get_route_parameters(route=route):

                annotation = cls.normalize_annotation(parameter.annotation)
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

                elif parameter_solved == 'primitive':
                    sw_type = cls.get_swagger_type(annotation if annotation is not inspect._empty else str)
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
                                'type': cls._swagger_type_name_from_annotation(field_type),
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
                                'type': cls._swagger_type_name_from_annotation(p.type),
                            }

                            if not isinstance(p.default, dataclasses._MISSING_TYPE):
                                properities[p.name]['default'] = p.default
                                continue

                            required.append(p.name)

                    master_props = {**master_props, **properities}
                    master_required.extend(required)
                elif parameter_solved == 'normal_class':
                    if cls.annotation_type_name(annotation) not in cls.mapping_swagger_types():
                        properities = {}
                        required = []

                        parameters = inspect.signature(annotation.__init__).parameters
                        for p, t in parameters.items():
                            if p.lower() not in ['self', 'cls']:
                                properities[p] = {
                                    'title': str(p).capitalize(),
                                    'type': cls._swagger_type_name_from_annotation(t.annotation)
                                }

                                if t.default != inspect._empty:
                                    properities[p]['default'] = t.default
                                    continue

                                required.append(p)

                        master_props = {**master_props, **properities}
                        master_required.extend(required)

                else:
                    if cls.annotation_type_name(annotation) not in cls.mapping_swagger_types():
                        properities = {}
                        required = []

                        if sys.version_info >= (3, 14):
                            import annotationlib
                            annotations = annotationlib.get_annotations(annotation)
                        else:
                            annotations = getattr(annotation, '__annotations__', {}) if isinstance(annotation, type) else {}

                        for p, t in annotations.items():
                            properities[p] = {
                                'title': str(p).capitalize(),
                                'type': cls._swagger_type_name_from_annotation(t)
                            }

                            if isinstance(annotation, type) and p in annotation.__dict__:
                                properities[p]['default'] = annotation.__dict__.get(p)
                                continue

                            required.append(p)

                        master_props = {**master_props, **properities}
                        master_required.extend(required)

                    else:
                        sw_type = cls.get_swagger_type(annotation if annotation is not inspect._empty else str)
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

        kwargs = dict(kwargs)
        all_callback_parameters = cls.get_callback_parameters(callback)
        kwd: dict[str, Any] = {}

        for name, parameter in all_callback_parameters.items():
            class_resolved = cls.resolve_class_type(parameter)
            annotation = cls.normalize_annotation(parameter.annotation)

            if class_resolved == 'file':
                if name in kwargs:
                    kwd[name] = kwargs.pop(name)[0]

            elif class_resolved in ['pydantic', 'dataclass', 'normal_class']:
                parameters = {}

                for key in cls.get_callback_parameters(annotation).keys():
                    parameters[key] = kwargs.pop(key)

                kwd[name] = annotation(**parameters)

            elif class_resolved == 'request':
                from pyweber.models.context import get_current_request
                request = kwargs.pop('request', None) or get_current_request()
                if request is None:
                    raise TypeError(
                        'Route handler requires a Request, but none is available. '
                        'Use app.request inside HTTP handlers or e.session context in WebSocket handlers.'
                    )
                kwd[name] = request

            elif class_resolved == 'primitive':
                if parameter.kind not in [inspect.Parameter.VAR_KEYWORD, inspect.Parameter.VAR_POSITIONAL]:
                    if name in kwargs:
                        raw = kwargs.pop(name)
                        kwd[name] = cls.coerce_value(name, raw, annotation)
                    elif parameter.default != inspect._empty:
                        kwd[name] = parameter.default

            else:
                type_name = cls.annotation_type_name(annotation)
                if type_name not in cls.mapping_swagger_types() and annotation is not inspect._empty:

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

    @classmethod
    def schema_for_type(cls, annotation: Any, registry: SchemaRegistry | None = None) -> dict[str, Any]:
        """Build a JSON Schema (optionally with $ref) for an annotation."""
        registry = registry or SchemaRegistry()
        annotation = cls.normalize_annotation(annotation)

        if annotation is inspect._empty or annotation is Any:
            return {'type': 'string'}

        if annotation is type(None):
            return {'nullable': True}

        origin = get_origin(annotation)
        args = get_args(annotation)

        # Union / Optional / PEP 604 (int | None)
        if _is_union_origin(origin):
            non_none = [a for a in args if a is not type(None)]
            has_none = len(non_none) != len(args)
            if not non_none:
                return {'nullable': True}
            schema = cls.schema_for_type(non_none[0], registry)
            if has_none:
                schema = {**schema, 'nullable': True}
            return schema

        if origin in (list, set, tuple):
            item = cls.schema_for_type(args[0], registry) if args else {'type': 'string'}
            return {'type': 'array', 'items': item}

        if origin is dict:
            value_schema = cls.schema_for_type(args[1], registry) if len(args) > 1 else {'type': 'string'}
            return {'type': 'object', 'additionalProperties': value_schema}

        if isinstance(annotation, type):
            type_name = annotation.__name__
            if type_name in cls.mapping_swagger_types():
                sw = cls.mapping_swagger_types()[type_name]
                return {'type': sw['type']}

            if hasattr(annotation, '__pydantic_validator__') or hasattr(annotation, 'model_json_schema'):
                try:
                    return registry.add_from_pydantic(annotation)
                except Exception:
                    pass

            if hasattr(annotation, '__dataclass_fields__'):
                return cls._dataclass_schema(annotation, registry)

            if hasattr(annotation, '__annotations__') and annotation.__annotations__:
                return cls._annotations_schema(annotation, registry)

            if hasattr(annotation, '__init__') and annotation.__init__ != object.__init__:
                return cls._init_schema(annotation, registry)

        name = cls.annotation_type_name(annotation)
        if name in cls.mapping_swagger_types():
            return {'type': cls.mapping_swagger_types()[name]['type']}

        return {'type': 'string'}

    @classmethod
    def _dataclass_schema(cls, model: type, registry: SchemaRegistry) -> dict[str, Any]:
        props = {}
        required = []
        for f in dataclasses.fields(model):
            props[f.name] = cls.schema_for_type(f.type, registry)
            if f.default is dataclasses.MISSING and f.default_factory is dataclasses.MISSING:
                required.append(f.name)
        schema = {'type': 'object', 'properties': props, 'title': model.__name__}
        if required:
            schema['required'] = required
        return registry.register(model.__name__, schema)

    @classmethod
    def _annotations_schema(cls, model: type, registry: SchemaRegistry) -> dict[str, Any]:
        annotations = getattr(model, '__annotations__', {}) or {}
        props = {}
        required = []
        for name, typ in annotations.items():
            props[name] = cls.schema_for_type(typ, registry)
            if not hasattr(model, name):
                required.append(name)
        schema = {'type': 'object', 'properties': props, 'title': getattr(model, '__name__', 'Model')}
        if required:
            schema['required'] = required
        return registry.register(getattr(model, '__name__', 'Model'), schema)

    @classmethod
    def _init_schema(cls, model: type, registry: SchemaRegistry) -> dict[str, Any]:
        props = {}
        required = []
        for name, param in inspect.signature(model.__init__).parameters.items():
            if name in ('self', 'cls'):
                continue
            props[name] = cls.schema_for_type(param.annotation, registry)
            if param.default is inspect._empty:
                required.append(name)
        schema = {'type': 'object', 'properties': props, 'title': model.__name__}
        if required:
            schema['required'] = required
        return registry.register(model.__name__, schema)

    @classmethod
    def get_return_annotation(cls, callback: Callable) -> Any:
        try:
            hints = __import__('typing').get_type_hints(callback, include_extras=True)
            if 'return' in hints:
                return cls.normalize_annotation(hints['return'])
        except Exception:
            pass
        ann = inspect.signature(callback).return_annotation
        return cls.normalize_annotation(ann)


class OpenAPIBuilder:
    """Build a live OpenAPI 3.0 document from app routes + OpenAPIConfig."""

    SKIP_PATHS = {'/docs'}

    def __init__(self, app: Any):
        self.app = app
        self.config: OpenAPIConfig = getattr(app, 'openapi', None) or OpenAPIConfig()

    def build(self) -> dict[str, Any]:
        registry = SchemaRegistry()
        paths: dict[str, Any] = {}
        tag_names: set[str] = set()

        for path in list(self.app.list_routes):
            if path in self.SKIP_PATHS:
                continue
            openapi_url = self.config.openapi_url
            if openapi_url and path == openapi_url:
                continue
            if path.startswith('/_pyweber/'):
                continue

            for route in self.app.get_routes_by_path(path, follow_redirect=False):
                if not getattr(route, 'include_in_schema', True):
                    continue
                self._add_route(paths, route, registry, tag_names)

        info: dict[str, Any] = {
            'title': self.config.title,
            'version': self.config.version,
        }
        if self.config.description:
            info['description'] = self.config.description
        if self.config.contact:
            info['contact'] = self.config.contact
        if self.config.license:
            info['license'] = self.config.license

        schema: dict[str, Any] = {
            'openapi': '3.0.0',
            'info': info,
            'paths': paths,
        }

        if self.config.servers:
            schema['servers'] = self.config.servers

        components: dict[str, Any] = {}
        if registry.schemas:
            components['schemas'] = registry.schemas
        sec_schemes = self.config.security_schemes_openapi()
        if sec_schemes:
            components['securitySchemes'] = sec_schemes
        if components:
            schema['components'] = components

        global_security = self.config.normalized_security()
        if global_security:
            schema['security'] = global_security

        tags = list(self.config.tags or [])
        existing = {t.get('name') for t in tags if isinstance(t, dict)}
        for name in sorted(tag_names):
            if name not in existing:
                tags.append({'name': name})
        if tags:
            schema['tags'] = tags

        return schema

    def _add_route(
        self,
        paths: dict[str, Any],
        route: Any,
        registry: SchemaRegistry,
        tag_names: set[str],
    ):
        from pyweber.models.routes import Route

        if not isinstance(route, Route):
            return

        path_key = route.full_route
        paths.setdefault(path_key, {})
        route_params_source = route.full_route_with_params

        tags = list(getattr(route, 'tags', None) or [])
        if not tags:
            group = route.group
            if group and group != Route.default_group() and not str(group).startswith('__'):
                tags = [str(group).removeprefix('__')]
        tag_names.update(tags)

        description = getattr(route, 'description', None)
        if not description and route.callback and route.callback.__doc__:
            description = inspect.cleandoc(route.callback.__doc__)

        response_model = getattr(route, 'response_model', None)
        if response_model is None and route.callback:
            ret = OpenApiProcessor.get_return_annotation(route.callback)
            if ret is not inspect._empty and ret is not Any and ret is not None:
                ret_name = OpenApiProcessor.annotation_type_name(ret)
                is_json = route.content_type == ContentTypes.json
                if ret_name in ('Template', 'Element', 'NoneType'):
                    pass
                elif ret_name in ('str', 'bytes') and not is_json:
                    pass
                else:
                    response_model = ret

        explicit_responses = dict(getattr(route, 'responses', None) or {})
        route_security = normalize_security_requirements(getattr(route, 'security', None))
        if route_security is None:
            route_security = self.config.normalized_security()

        content_type = route.content_type.value if hasattr(route.content_type, 'value') else str(route.content_type)

        for method in route.methods:
            operation: dict[str, Any] = {
                'summary': route.title or 'Pyweber Route',
                'parameters': [
                    v for _, v in OpenApiProcessor.get_route_spec(route_params_source, route.callback).items()
                ],
                'responses': self._build_responses(
                    route=route,
                    response_model=response_model,
                    explicit=explicit_responses,
                    content_type=content_type,
                    registry=registry,
                    has_security=bool(route_security),
                ),
            }

            if description:
                operation['description'] = description
            if tags:
                operation['tags'] = tags
            if getattr(route, 'deprecated', False):
                operation['deprecated'] = True

            operation_id = getattr(route, 'operation_id', None) or route.name
            if not operation_id:
                safe_path = re.sub(r'[{}/]', '_', path_key).strip('_')
                operation_id = f'{method.lower()}_{safe_path}'
            operation['operationId'] = operation_id

            if route_security is not None:
                operation['security'] = route_security

            request_body = OpenApiProcessor.get_body_spec(route_params_source, route.callback)
            if request_body.get('content') and getattr(route.callback, '__name__', '') != '<lambda>':
                operation['requestBody'] = self._upgrade_body_refs(request_body, route, registry)

            paths[path_key][method.lower()] = operation

    def _build_responses(
        self,
        route: Any,
        response_model: Any,
        explicit: dict,
        content_type: str,
        registry: SchemaRegistry,
        has_security: bool,
    ) -> dict[str, Any]:
        responses: dict[str, Any] = {}

        success_code = str(route.status_code)
        success: dict[str, Any] = {
            'description': HTTPStatusCode.search_name_by_code(route.status_code) or 'Success',
        }
        if response_model is not None and response_model is not inspect._empty:
            success['content'] = {
                content_type: {
                    'schema': OpenApiProcessor.schema_for_type(response_model, registry)
                }
            }
        responses[success_code] = success

        for code, spec in explicit.items():
            key = str(code)
            if isinstance(spec, type) or (not isinstance(spec, dict) and spec is not None and hasattr(spec, '__name__')):
                responses[key] = {
                    'description': HTTPStatusCode.search_name_by_code(int(code)) if str(code).isdigit() else 'Response',
                    'content': {
                        content_type: {
                            'schema': OpenApiProcessor.schema_for_type(spec, registry)
                        }
                    },
                }
            elif isinstance(spec, dict):
                entry = dict(spec)
                model = entry.pop('model', None)
                if model is not None:
                    media = entry.pop('content_type', content_type)
                    entry.setdefault('content', {})
                    entry['content'][media] = {
                        'schema': OpenApiProcessor.schema_for_type(model, registry)
                    }
                entry.setdefault(
                    'description',
                    HTTPStatusCode.search_name_by_code(int(code)) if str(code).isdigit() else 'Response',
                )
                responses[key] = entry
            else:
                responses[key] = {'description': str(spec)}

        if has_security:
            responses.setdefault('401', {'description': 'Unauthorized'})
            responses.setdefault('403', {'description': 'Forbidden'})

        responses.setdefault('500', {'description': HTTPStatusCode.search_name_by_code(500)})
        return responses

    def _upgrade_body_refs(self, request_body: dict, route: Any, registry: SchemaRegistry) -> dict:
        """Prefer $ref for pydantic/dataclass body parameters when possible."""
        try:
            from pyweber.models.routes import Route
            route_params = set(OpenApiProcessor.get_route_parameters(route.full_route_with_params))
            for name, parameter in OpenApiProcessor.get_callback_parameters(route.callback).items():
                if name in route_params:
                    continue
                kind = OpenApiProcessor.resolve_class_type(parameter)
                annotation = OpenApiProcessor.normalize_annotation(parameter.annotation)
                if kind in ('pydantic', 'dataclass', 'normal_class') and isinstance(annotation, type):
                    ref = OpenApiProcessor.schema_for_type(annotation, registry)
                    # Replace flat props with a single $ref body when one model param
                    return {
                        'description': request_body.get('description', 'Request Body'),
                        'required': request_body.get('required', True),
                        'content': {
                            media: {'schema': ref}
                            for media in request_body.get('content', {})
                        },
                    }
        except Exception:
            pass
        return request_body
