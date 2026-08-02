"""OpenAPI builder, config, and security enforcement tests."""

import dataclasses
import pytest

from pyweber.pyweber.pyweber import Pyweber
from pyweber.models.request import Request, ClientInfo
from pyweber.models.response import Response
from pyweber.models.openapi import OpenAPIConfig, OpenAPIBuilder, OpenApiProcessor
from pyweber.models.security import (
    HTTPBearer,
    APIKeyHeader,
    ForbiddenError,
    normalize_security_requirements,
)
from pyweber.utils.types import ContentTypes


def _request(method: str, path: str, extra_headers: str = '') -> Request:
    headers = f'{method} {path} HTTP/1.1\r\nHost: localhost\r\n{extra_headers}\r\n'
    return Request(
        headers=headers,
        body=b'',
        client_info=ClientInfo(host='127.0.0.1', port=1),
    )


@dataclasses.dataclass
class UserOut:
    id: int
    name: str


class TestOpenAPIBuilder:
    def test_schema_includes_info_tags_operation_and_full_route(self):
        app = Pyweber(
            openapi=OpenAPIConfig(
                title='Demo API',
                version='2.0.0',
                description='Demo',
                servers=[{'url': 'http://localhost'}],
            )
        )

        @app.route(
            '/users/{user_id}',
            methods=['GET'],
            group='api',
            title='Get user',
            tags=['users'],
            name='get_user',
            response_model=UserOut,
            responses={404: {'description': 'Not found'}},
            content_type=ContentTypes.json,
        )
        def get_user(user_id: int) -> UserOut:
            """Fetch a user by id."""
            return UserOut(id=user_id, name='x')

        schema = app.get_openapi_schema()

        assert schema['info']['title'] == 'Demo API'
        assert schema['info']['version'] == '2.0.0'
        assert schema['servers'][0]['url'] == 'http://localhost'
        assert '/api/users/{user_id}' in schema['paths']
        op = schema['paths']['/api/users/{user_id}']['get']
        assert op['operationId'] == 'get_user'
        assert op['tags'] == ['users']
        assert 'Fetch a user by id.' in op['description']
        assert '404' in op['responses']
        assert '200' in op['responses']
        assert 'content' in op['responses']['200']
        assert 'users' in {t['name'] for t in schema['tags']}

    def test_security_schemes_in_components(self):
        def verify_token(credentials):
            return credentials == 'secret'

        app = Pyweber(
            openapi=OpenAPIConfig(
                security_schemes={'BearerAuth': HTTPBearer(verify=verify_token)},
                security=['BearerAuth'],
            )
        )
        app.add_route(
            route='/private',
            template=lambda **kw: {'ok': True},
            methods=['GET'],
            content_type=ContentTypes.json,
            security=['BearerAuth'],
        )

        schema = app.get_openapi_schema()
        assert 'BearerAuth' in schema['components']['securitySchemes']
        assert schema['security'] == [{'BearerAuth': []}]
        assert schema['paths']['/private']['get']['security'] == [{'BearerAuth': []}]
        assert '401' in schema['paths']['/private']['get']['responses']

    def test_dataclass_response_registers_components_schema(self):
        app = Pyweber()
        app.add_route(
            route='/me',
            template=lambda **kw: {'id': 1, 'name': 'a'},
            methods=['GET'],
            content_type=ContentTypes.json,
            response_model=UserOut,
        )
        schema = app.get_openapi_schema()
        ref = schema['paths']['/me']['get']['responses']['200']['content'][ContentTypes.json.value]['schema']
        assert '$ref' in ref
        assert 'UserOut' in schema['components']['schemas']

    def test_include_in_schema_false_hides_route(self):
        app = Pyweber()
        app.add_route(route='/hidden', template='x', methods=['GET'], include_in_schema=False)
        schema = app.get_openapi_schema()
        assert '/hidden' not in schema['paths']


class TestDocsUrls:
    @pytest.mark.asyncio
    async def test_default_docs_and_openapi_json(self):
        app = Pyweber()
        docs = await app.get_response(_request('GET', '/docs'))
        openapi = await app.get_response(_request('GET', '/openapi.json'))
        assert docs.status_code == 200
        assert openapi.status_code == 200
        assert b'openapi' in openapi.response_content

    @pytest.mark.asyncio
    async def test_docs_disabled(self):
        app = Pyweber(openapi=OpenAPIConfig(docs_url=None, openapi_url=None))
        docs = await app.get_response(_request('GET', '/docs'))
        openapi = await app.get_response(_request('GET', '/openapi.json'))
        assert docs.status_code == 404
        assert openapi.status_code == 404


class TestSecurityEnforcement:
    @pytest.mark.asyncio
    async def test_bearer_required_returns_401(self):
        app = Pyweber(
            openapi=OpenAPIConfig(
                security_schemes={'BearerAuth': HTTPBearer(verify=lambda credentials: credentials == 'ok')},
            )
        )
        app.add_route(
            route='/secure',
            template=lambda **kw: {'ok': True},
            methods=['GET'],
            content_type=ContentTypes.json,
            security=['BearerAuth'],
        )

        resp = await app.get_response(_request('GET', '/secure'))
        assert resp.status_code == 401
        assert resp.headers.get('WWW-Authenticate') == 'Bearer'

    @pytest.mark.asyncio
    async def test_plain_401_has_no_www_authenticate(self):
        app = Pyweber()

        @app.route('/denied', methods=['GET'], content_type=ContentTypes.json)
        def denied():
            return Response.json({'detail': 'no'}, status=401)

        resp = await app.get_response(_request('GET', '/denied'))
        assert resp.status_code == 401
        assert 'WWW-Authenticate' not in resp.headers

    @pytest.mark.asyncio
    async def test_bearer_valid_returns_200_and_sets_auth(self):
        seen = {}

        def verify(credentials):
            return {'sub': 'user-1'} if credentials == 'token123' else False

        app = Pyweber(
            openapi=OpenAPIConfig(
                security_schemes={'BearerAuth': HTTPBearer(verify=verify)},
            )
        )

        @app.route('/secure', methods=['GET'], content_type=ContentTypes.json, security=['BearerAuth'])
        def secure(request: Request):
            seen['auth'] = request.auth
            return {'ok': True}

        resp = await app.get_response(
            _request('GET', '/secure', extra_headers='Authorization: Bearer token123\r\n')
        )
        assert resp.status_code == 200
        assert seen['auth'] is not None
        assert seen['auth'].user == {'sub': 'user-1'}

    @pytest.mark.asyncio
    async def test_verify_false_returns_401(self):
        app = Pyweber(
            openapi=OpenAPIConfig(
                security_schemes={'BearerAuth': HTTPBearer(verify=lambda credentials: False)},
            )
        )
        app.add_route(
            route='/secure',
            template=lambda **kw: {'ok': True},
            methods=['GET'],
            content_type=ContentTypes.json,
            security=['BearerAuth'],
        )
        resp = await app.get_response(
            _request('GET', '/secure', extra_headers='Authorization: Bearer bad\r\n')
        )
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_forbidden_error_returns_403(self):
        def verify(credentials):
            raise ForbiddenError('nope')

        app = Pyweber(
            openapi=OpenAPIConfig(
                security_schemes={'BearerAuth': HTTPBearer(verify=verify)},
            )
        )
        app.add_route(
            route='/secure',
            template=lambda **kw: {'ok': True},
            methods=['GET'],
            content_type=ContentTypes.json,
            security=['BearerAuth'],
        )
        resp = await app.get_response(
            _request('GET', '/secure', extra_headers='Authorization: Bearer x\r\n')
        )
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_empty_security_ignores_global(self):
        app = Pyweber(
            openapi=OpenAPIConfig(
                security_schemes={'BearerAuth': HTTPBearer()},
                security=['BearerAuth'],
            )
        )
        app.add_route(
            route='/public',
            template=lambda **kw: {'ok': True},
            methods=['GET'],
            content_type=ContentTypes.json,
            security=[],
        )
        resp = await app.get_response(_request('GET', '/public'))
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_api_key_header(self):
        app = Pyweber(
            openapi=OpenAPIConfig(
                security_schemes={
                    'ApiKeyAuth': APIKeyHeader(name='X-API-Key', verify=lambda credentials: credentials == 'k')
                },
            )
        )
        app.add_route(
            route='/keyed',
            template=lambda **kw: {'ok': True},
            methods=['GET'],
            content_type=ContentTypes.json,
            security=['ApiKeyAuth'],
        )
        missing = await app.get_response(_request('GET', '/keyed'))
        ok = await app.get_response(_request('GET', '/keyed', extra_headers='X-API-Key: k\r\n'))
        assert missing.status_code == 401
        assert ok.status_code == 200


def test_normalize_security_requirements():
    assert normalize_security_requirements(None) is None
    assert normalize_security_requirements([]) == []
    assert normalize_security_requirements(['BearerAuth']) == [{'BearerAuth': []}]
    assert normalize_security_requirements([{'BearerAuth': ['read']}]) == [{'BearerAuth': ['read']}]


def test_schema_for_optional_and_list():
    schema = OpenApiProcessor.schema_for_type(list[int])
    assert schema['type'] == 'array'
    assert schema['items']['type'] == 'integer'

    opt = OpenApiProcessor.schema_for_type(int | None)
    assert opt.get('type') == 'integer'
    assert opt.get('nullable') is True
