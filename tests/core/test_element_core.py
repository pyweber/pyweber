import pytest

from pyweber.core.element import Element, GetBy
from pyweber.core.template import Template


def test_element_from_html_and_query():
    root = Element.from_html('<html><body><p id="a" class="x">Hi</p></body></html>')
    assert root.tag == 'html'
    found = root.querySelector('#a')
    assert found.content == 'Hi'
    assert root.querySelectorAll('p')


def test_element_get_by_methods():
    el = Element('div', attrs={'id': 'box', 'class': 'a b'}, content='text')
    assert el.getElement(by=GetBy.tag, value='div') is el
    assert el.getElements(by=GetBy.tag, value='div')


def test_element_to_html_with_child():
    parent = Element('ul', childs=[Element('li', content='1'), Element('li', content='2')])
    html = parent.to_html()
    assert 'li' in html
    assert html.count('1') >= 1


def test_template_parse_and_build():
    tpl = Template(template='<body><h1>Title</h1></body>', title='My Page')
    html = tpl.build_html()
    assert '<!DOCTYPE html>' in html
    assert 'Title' in html
    assert tpl.head is not None
    assert tpl.body is not None


def test_template_query_helpers():
    tpl = Template(template='<body><span class="item">A</span><span class="item">B</span></body>')
    assert tpl.querySelector('.item') is not None
    assert len(tpl.querySelectorAll('.item')) >= 1


def test_element_invalid_root_raises():
    tpl = Template(template='<body>x</body>')
    with pytest.raises(ValueError):
        tpl.root = Element('div')
