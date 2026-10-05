"""Swagger grouping, summaries, login_required security and the /docs page."""

from __future__ import annotations

import json

import pytest

import pyweber as pw
from pyweber.auth import login_required
from pyweber.models.openapi import OpenAPIConfig
from pyweber.testing.client import TestClient


def _schema(app):
    return app.get_openapi_schema()


def test_untagged_routes_are_grouped_by_first_path_segment():
    app = pw.Pyweber()

    @app.route('/admin/estrutura/departamentos')
    def listar_departamentos():
        return 'ok'

    @app.route('/{slug}/perfil')
    def perfil(slug: str):
        return 'ok'

    @app.route('/users', tags=['Utilizadores'])
    def users():
        return 'ok'

    paths = _schema(app)['paths']
    assert paths['/admin/estrutura/departamentos']['get']['tags'] == ['admin']
    assert paths['/{slug}/perfil']['get']['tags'] == ['perfil']
    assert paths['/users']['get']['tags'] == ['Utilizadores']
    assert {'admin', 'perfil', 'Utilizadores'} <= {t['name'] for t in _schema(app)['tags']}


def test_auto_tags_can_be_disabled():
    app = pw.Pyweber(openapi=OpenAPIConfig(auto_tags=False))

    @app.route('/admin/x')
    def x():
        return 'ok'

    assert 'tags' not in _schema(app)['paths']['/admin/x']['get']


def test_summary_falls_back_to_docstring_then_function_name():
    app = pw.Pyweber()

    @app.route('/a')
    def a():
        """Lista os departamentos.

        Detalhes longos.
        """
        return 'ok'

    @app.route('/b')
    def listar_unidades():
        return 'ok'

    @app.route('/c', title='Título explícito')
    def c():
        return 'ok'

    paths = _schema(app)['paths']
    assert paths['/a']['get']['summary'] == 'Lista os departamentos.'
    assert paths['/b']['get']['summary'] == 'Listar unidades'
    assert paths['/c']['get']['summary'] == 'Título explícito'


def test_login_required_routes_document_session_cookie():
    app = pw.Pyweber()

    @app.route('/painel')
    @login_required(roles=['admin'])
    def painel():
        return 'ok'

    @app.route('/publico')
    def publico():
        return 'ok'

    schema = _schema(app)
    operation = schema['paths']['/painel']['get']
    assert operation['security'] == [{'PyweberSession': []}]
    assert 'Requires login' in operation['description']
    assert '`admin`' in operation['description']
    assert 'security' not in schema['paths']['/publico']['get']

    scheme = schema['components']['securitySchemes']['PyweberSession']
    assert scheme == {**scheme, 'type': 'apiKey', 'in': 'cookie', 'name': 'pyweber_user'}


def test_login_required_is_an_alternative_to_declared_schemes():
    app = pw.Pyweber(openapi=OpenAPIConfig(
        security_schemes={'BearerAuth': pw.HTTPBearer()},
    ))

    @app.route('/me', security=['BearerAuth'])
    @login_required
    def me():
        return 'ok'

    security = _schema(app)['paths']['/me']['get']['security']
    assert security == [{'BearerAuth': []}, {'PyweberSession': []}]


@pytest.mark.asyncio
async def test_docs_page_uses_config_and_sends_csrf():
    app = pw.Pyweber(openapi=OpenAPIConfig(
        title='Minha <API>',
        openapi_url='/api/schema.json',
        swagger_ui_parameters={'docExpansion': 'none'},
    ))

    response = await TestClient(app).get('/docs')
    body = response.response_content.decode('utf-8')

    assert response.status_code == 200
    assert '<title>Minha &lt;API&gt;</title>' in body
    assert 'X-CSRF-Token' in body and 'pyweber_csrf' in body

    options = json.loads(body.split('const options = ', 1)[1].split(';\n', 1)[0])
    assert options['url'] == '/api/schema.json'
    assert options['docExpansion'] == 'none'
    assert options['persistAuthorization'] is True
    assert options['filter'] is True
