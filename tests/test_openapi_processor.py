
import unittest
import inspect
from dataclasses import dataclass

# Mock para Pydantic BaseModel
class MockBaseModel:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    @classmethod
    def model_json_schema(cls):
        return {
            'properties': {
                'username': {'type': 'string', 'title': 'Username'},
                'email': {'type': 'string', 'title': 'Email'},
                'age': {'type': 'integer', 'title': 'Age', 'default': 25}
            },
            'required': ['username', 'email']
        }

    def __pydantic_validator__(self):
        pass

# Mock para ContentTypes
class ContentTypes:
    class json:
        value = 'application/json'

# Simulando a classe OpenApiProcessor (sem imports externos)
import re

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
    def default_format_types(type_name: str):
        return {'string': None, 'integer': 'int32', 'float': 'float', 'boolean': 'boolean'}.get(type_name, None)

    @staticmethod
    def get_swegger_types(py_type: type, format_type: str = None):
        mapping_types = OpenApiProcessor.mapping_swegger_types()
        swegger_type = mapping_types.get(py_type.__name__, mapping_types['str'])
        return {'type': {'type': swegger_type['type'], 'format': format_type if format_type in swegger_type.get('formats', []) else None}}

    @staticmethod
    def is_valid_route_param_type(py_type: str):
        return py_type in ['str', 'int', 'float', 'bool']

    @classmethod
    def resolve_class_type(cls, parameter: inspect.Parameter):
        annotation = parameter.annotation

        if hasattr(annotation, '__pydantic_validator__'):
            return 'pydantic'

        if hasattr(annotation, '__dataclass_fields__'):
            return 'dataclass'

        if hasattr(annotation, '__init__') and annotation.__init__ != object.__init__:
            return 'normal_class'

        return 'empty_class'

    @classmethod
    def get_route_parameters(cls, route: str) -> list[str]:
        return re.findall(r"{\s*(.*?)\s*}", route)

    @classmethod
    def get_callback_parameters(cls, callback):
        return {param.name: param for param in inspect.signature(callback).parameters.values()}


class TestOpenApiProcessor(unittest.TestCase):

    def setUp(self):
        self.processor = OpenApiProcessor()

    def test_get_format_example_known_formats(self):
        """Test format examples for known formats"""
        self.assertEqual(self.processor.get_format_example('date'), '2023-12-25')
        self.assertEqual(self.processor.get_format_example('email'), 'user@example.com')
        self.assertEqual(self.processor.get_format_example('uuid'), '550e8400-e29b-41d4-a716-446655440000')
        self.assertEqual(self.processor.get_format_example('int32'), 2147483647)
        self.assertEqual(self.processor.get_format_example('bool'), True)

    def test_get_format_example_unknown_format(self):
        """Test format example for unknown format returns default"""
        self.assertEqual(self.processor.get_format_example('unknown_format'), 'pyweber')

    def test_mapping_swegger_types(self):
        """Test swagger types mapping"""
        mapping = self.processor.mapping_swegger_types()

        self.assertEqual(mapping['str']['type'], 'string')
        self.assertEqual(mapping['int']['type'], 'integer')
        self.assertEqual(mapping['float']['type'], 'number')
        self.assertEqual(mapping['bool']['type'], 'boolean')
        self.assertEqual(mapping['list']['type'], 'array')
        self.assertEqual(mapping['dict']['type'], 'object')

        # Test formats
        self.assertIn('email', mapping['str']['formats'])
        self.assertIn('int32', mapping['int']['formats'])
        self.assertEqual(mapping['bool']['formats'], [])

    def test_default_format_types(self):
        """Test default format types"""
        self.assertIsNone(self.processor.default_format_types('string'))
        self.assertEqual(self.processor.default_format_types('integer'), 'int32')
        self.assertEqual(self.processor.default_format_types('float'), 'float')
        self.assertEqual(self.processor.default_format_types('boolean'), 'boolean')
        self.assertIsNone(self.processor.default_format_types('unknown'))

    def test_get_swegger_types_basic_types(self):
        """Test swagger type conversion for basic Python types"""
        # String type
        result = self.processor.get_swegger_types(str)
        self.assertEqual(result['type']['type'], 'string')
        self.assertIsNone(result['type']['format'])

        # Integer type
        result = self.processor.get_swegger_types(int)
        self.assertEqual(result['type']['type'], 'integer')
        self.assertIsNone(result['type']['format'])

        # Boolean type
        result = self.processor.get_swegger_types(bool)
        self.assertEqual(result['type']['type'], 'boolean')
        self.assertIsNone(result['type']['format'])

    def test_get_swegger_types_with_format(self):
        """Test swagger type conversion with specific format"""
        result = self.processor.get_swegger_types(str, 'email')
        self.assertEqual(result['type']['type'], 'string')
        self.assertEqual(result['type']['format'], 'email')

        # Invalid format should return None
        result = self.processor.get_swegger_types(str, 'invalid_format')
        self.assertEqual(result['type']['type'], 'string')
        self.assertIsNone(result['type']['format'])

    def test_is_valid_route_param_type(self):
        """Test route parameter type validation"""
        self.assertTrue(self.processor.is_valid_route_param_type('str'))
        self.assertTrue(self.processor.is_valid_route_param_type('int'))
        self.assertTrue(self.processor.is_valid_route_param_type('float'))
        self.assertTrue(self.processor.is_valid_route_param_type('bool'))

        self.assertFalse(self.processor.is_valid_route_param_type('list'))
        self.assertFalse(self.processor.is_valid_route_param_type('dict'))
        self.assertFalse(self.processor.is_valid_route_param_type('custom_class'))

    def test_resolve_class_type_pydantic(self):
        """Test class type resolution for Pydantic models"""
        def dummy_func(user: MockBaseModel):
            pass

        sig = inspect.signature(dummy_func)
        param = sig.parameters['user']

        result = self.processor.resolve_class_type(param)
        self.assertEqual(result, 'pydantic')

    def test_resolve_class_type_dataclass(self):
        """Test class type resolution for dataclasses"""
        @dataclass
        class TestDataclass:
            name: str
            age: int = 25

        def dummy_func(data: TestDataclass):
            pass

        sig = inspect.signature(dummy_func)
        param = sig.parameters['data']

        result = self.processor.resolve_class_type(param)
        self.assertEqual(result, 'dataclass')

    def test_resolve_class_type_normal_class(self):
        """Test class type resolution for normal classes"""
        class NormalClass:
            def __init__(self, name: str):
                self.name = name

        def dummy_func(obj: NormalClass):
            pass

        sig = inspect.signature(dummy_func)
        param = sig.parameters['obj']

        result = self.processor.resolve_class_type(param)
        self.assertEqual(result, 'normal_class')

    def test_resolve_class_type_empty_class(self):
        """Test class type resolution for empty classes"""
        class EmptyClass:
            pass

        def dummy_func(obj: EmptyClass):
            pass

        sig = inspect.signature(dummy_func)
        param = sig.parameters['obj']

        result = self.processor.resolve_class_type(param)
        self.assertEqual(result, 'empty_class')

    def test_get_route_parameters(self):
        """Test route parameter extraction"""
        # Single parameter
        result = self.processor.get_route_parameters('/users/{id}')
        self.assertEqual(result, ['id'])

        # Multiple parameters
        result = self.processor.get_route_parameters('/users/{user_id}/posts/{post_id}')
        self.assertEqual(result, ['user_id', 'post_id'])

        # No parameters
        result = self.processor.get_route_parameters('/users')
        self.assertEqual(result, [])

        # Parameters with spaces
        result = self.processor.get_route_parameters('/users/{ id }/posts/{ post_id }')
        self.assertEqual(result, ['id', 'post_id'])

    def test_get_callback_parameters(self):
        """Test callback parameter extraction"""
        def test_function(id: int, name: str, age: int = 25):
            pass

        result = self.processor.get_callback_parameters(test_function)

        self.assertIn('id', result)
        self.assertIn('name', result)
        self.assertIn('age', result)
        self.assertEqual(len(result), 3)

        # Check parameter details
        self.assertEqual(result['id'].annotation, int)
        self.assertEqual(result['name'].annotation, str)
        self.assertEqual(result['age'].default, 25)

    def test_get_callback_parameters_no_params(self):
        """Test callback parameter extraction for function with no parameters"""
        def test_function():
            pass

        result = self.processor.get_callback_parameters(test_function)
        self.assertEqual(len(result), 0)

if __name__ == '__main__':
    # Executar os testes
    unittest.main(verbosity=2)
