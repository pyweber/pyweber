"""SchemaRegistry and extra OpenApiProcessor branch coverage."""

from typing import Optional, Union, get_args
from unittest.mock import MagicMock

import pytest

from pyweber.models.openapi import SchemaRegistry, OpenApiProcessor


class TestSchemaRegistry:
    def test_register_and_unique_name(self):
        reg = SchemaRegistry()
        ref1 = reg.register('User', {'type': 'object', 'properties': {'id': {'type': 'integer'}}})
        ref2 = reg.register('User', {'type': 'object', 'properties': {'name': {'type': 'string'}}})
        assert ref1['$ref'].endswith('/User')
        assert ref2['$ref'].endswith('/User_1')
        assert 'User' in reg.schemas
        assert 'User_1' in reg.schemas

    def test_add_from_pydantic_with_defs(self):
        reg = SchemaRegistry()

        class Model:
            __name__ = 'Model'

            @classmethod
            def model_json_schema(cls):
                return {
                    'type': 'object',
                    'properties': {'nested': {'$ref': '#/$defs/Inner'}},
                    '$defs': {
                        'Inner': {
                            'type': 'object',
                            'properties': {'x': {'type': 'string'}},
                        }
                    },
                }

        ref = reg.add_from_pydantic(Model)
        assert '$ref' in ref
        assert 'Inner' in reg.schemas

    def test_rewrite_refs_definitions_and_list(self):
        node = {
            'oneOf': [
                {'$ref': '#/definitions/A'},
                {'type': 'string'},
            ]
        }
        out = SchemaRegistry._rewrite_refs(node)
        assert out['oneOf'][0]['$ref'] == '#/components/schemas/A'


class TestOpenApiNormalizeExtra:
    def test_normalize_empty_and_none(self):
        assert OpenApiProcessor.normalize_annotation(None) is type(None)
        assert OpenApiProcessor.normalize_annotation('') is str or OpenApiProcessor._resolve_string_annotation('') is str
        assert OpenApiProcessor._resolve_string_annotation('') is str
        assert OpenApiProcessor._resolve_string_annotation('Union[int, str]') is int
        assert OpenApiProcessor._resolve_string_annotation('Literal["a"]') is str
        assert OpenApiProcessor._resolve_string_annotation('dict[str, int]') is dict
        assert OpenApiProcessor._resolve_string_annotation('CustomThing') is str

    def test_normalize_forward_ref(self):
        fr = MagicMock()
        fr.__forward_arg__ = 'int'
        assert OpenApiProcessor.normalize_annotation(fr) is int

    def test_annotation_type_name_union(self):
        name = OpenApiProcessor.annotation_type_name(Optional[int])
        assert name in ('int', 'Optional')
        name2 = OpenApiProcessor.annotation_type_name(Union[str, None])
        assert name2 in ('str', 'Union')

    def test_resolve_class_type_file_and_request(self):
        import inspect
        from pyweber.models.request import Request
        from pyweber.models.file import File

        def f(f: File, r: Request):
            pass

        params = inspect.signature(f).parameters
        assert OpenApiProcessor.resolve_class_type(params['f']) == 'file'
        assert OpenApiProcessor.resolve_class_type(params['r']) == 'request'
