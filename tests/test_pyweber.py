import pytest
from pyweber.core.template import Template
from pyweber.pyweber.pyweber import Pyweber
from pyweber.core.element import Element

@pytest.fixture
def app():
    return Pyweber()

# error pages
def test_cookies(app):
    assert len(app.cookies) == 0

def test_get_before_middlewares(app):
    assert len(app.get_before_request_middlewares) == 0

def test_get_after_middlewares(app):
    assert len(app.get_after_request_middlewares) == 0

def test_list_routes(app):
    assert '/admin' in app.list_routes

def test_redirected_list_routes(app):
    assert len(app.list_redirected_routes) == 0

def test_exists(app):
    assert app.exists('/admin')

def test_template_to_bytes(app):
    assert isinstance(app.template_to_bytes(template='Hello world').content, bytes)
    assert isinstance(app.template_to_bytes(template=Template(template='Hello world')).content, bytes)
    assert isinstance(app.template_to_bytes(template={'message': 'Hello world'}).content, bytes)
    assert isinstance(app.template_to_bytes(template=Element(tag='p', content='Hello world')).content, bytes)
    assert isinstance(app.template_to_bytes(template=b'Hello world').content, bytes)