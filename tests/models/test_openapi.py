from pyweber.models.openapi import OpenApiProcessor
import pytest
import inspect
import dataclasses

class MockBaseModel:
    def __init__(value: str): pass

    @classmethod
    def __pydantic_validator__(cls): pass

    @classmethod
    def model_json_schema(cls):
        return {'properties': {'value': {'title': 'Value', 'type': 'string'}}, 'required': ['value']}

@dataclasses.dataclass
class MockDataclass:
    user: str
    age: int = 20

class MockNormalClass:
    def __init__(self, name: str, idade: int = 40): pass

class MockEmptyClass:
    status: bool
    perfil: str = 'active'

@pytest.fixture
def openapi():
    return OpenApiProcessor()

def test_get_format_examples(openapi):
    assert isinstance(openapi.mapping_swagger_types(), dict)

def test_default_format_types(openapi):
    assert openapi.default_format_type('integer') == 'int32'

def test_get_format_example(openapi):
    assert openapi.get_format_example('hostname') == 'docs.pyweber.dev'

def test_swagger_types(openapi):
    assert openapi.get_swagger_type(float, 'double')['type'] == {'type': 'number', 'format': 'double'}

def test_is_valid_route_param_type(openapi):
    assert openapi.is_valid_route_param_type('str')

def test_resolve_class_type(openapi):
    def example_func_1(arg: MockBaseModel): pass
    def example_func_2(arg: MockDataclass): pass
    def example_func_3(arg: MockNormalClass): pass
    def example_func_4(arg: MockEmptyClass): pass

    assert openapi.resolve_class_type(inspect.signature(example_func_1).parameters.get('arg')) == 'pydantic'
    assert openapi.resolve_class_type(inspect.signature(example_func_2).parameters.get('arg')) == 'dataclass'
    assert openapi.resolve_class_type(inspect.signature(example_func_3).parameters.get('arg')) == 'normal_class'
    assert openapi.resolve_class_type(inspect.signature(example_func_4).parameters.get('arg')) == 'empty_class'

def test_get_type_parameter(openapi):
    def example_func(id, name: int): pass
    parameters = inspect.signature(example_func).parameters

    assert openapi.get_type_parameter(parameters['id'])['type'] == {'type': 'string', 'format': None}
    assert openapi.get_type_parameter(parameters['name'])['type'] == {'type': 'integer', 'format': None}

def test_get_route_parameters(openapi):
    assert openapi.get_route_parameters('/example/{id}/{name}') == ['id', 'name']

def test_get_callback_parameters(openapi):
    def example_func(id: int, name: str): pass
    parameters = inspect.signature(example_func).parameters

    assert openapi.get_callback_parameters(example_func) == {'id': parameters['id'], 'name': parameters['name']}

def test_get_route_spec(openapi):
    def example_func(name: str, id: int = 1): pass

    response = {
        'name': {
            'name': 'name',
            'in': 'path',
            'required': True,
            'schema': {
                'type': 'string',
                'format': None
            },
            'example': 'pyweber'
        },
        'id': {
            'name': 'id',
            'in': 'path',
            'schema': {
                'type': 'integer',
                'format': None
            },
            'example': 2147483647,
            'default': 1
        },
        'topic': {
            'name': 'topic',
            'in': 'path',
            'required': True,
            'schema': {
                'type': 'string',
                'format': None
            },
            'example': 'pyweber'
        }
    }

    assert openapi.get_route_spec('/example/{id}/{name}/{topic}', example_func) == response

def test_get_get_body_spec(openapi):
    def example_func(
        id: str,
        name: str,
        user_1: MockBaseModel,
        user_2: MockDataclass,
        user_3: MockNormalClass,
        user_4: MockEmptyClass,
        number: int = 14
    ): pass

    assert openapi.get_body_spec('/example/{id}', example_func)

def test_prepare_callback_kwargs(openapi):
    kwargs = {
        'id': 20,
        'name': 'azunguze',
        'value': 'value2',
        'age': 20,
        'user': 'pyweberuser',
        'idade': 15,
        'status': False,
        'perfil': 'pyweber'
    }

    def example_func(
        id: int,
        user_1: MockBaseModel,
        user_2: MockDataclass,
        user_3: MockNormalClass,
        user_4: MockEmptyClass
    ): pass

    response_user_keys = ['id', 'user_1', 'user_2', 'user_3', 'user_4', 'kwargs']

    assert list(openapi.prepare_callback_kwargs(example_func, **kwargs).keys()) == response_user_keys