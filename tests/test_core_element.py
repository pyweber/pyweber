from pyweber.core.element import Element
from clear_pycache import clear_cache
import pytest

@pytest.fixture
def element():
    elm = Element(
        tag='html',
        id='html',
        classes=['html'],
        attrs={'lang': 'pt-BR'},
        parent=None,
        childs=[
            Element(
                name='head',
                childs=[
                    Element(
                        name='title',
                        content='Tests'
                    )
                ]
            )
        ]
    )

    yield elm

    clear_cache() # clear pycache


def test_name(element: Element):
    assert element.name == 'html'

def test_id(element: Element):
    assert element.id == 'html'

def test_classes(element: Element):
    assert element.classes == ['html']

def test_uuid(element: Element):
    assert element.uuid is not None