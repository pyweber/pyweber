"""Tests for pluggable HTML parse backends."""

import pytest

from pyweber.core.element import Element
from pyweber.core.html_parser import (
    StdlibHtmlBackend,
    parse_html,
    reset_html_parser_backend,
    set_html_parser_backend,
)


@pytest.fixture(autouse=True)
def _reset_parser_backend():
    reset_html_parser_backend()
    yield
    reset_html_parser_backend()


def test_stdlib_backend_is_default():
    backend = set_html_parser_backend('stdlib')
    assert backend.name == 'stdlib'
    root = parse_html('<div id="x">ok</div>')
    assert root.tag == 'div'
    assert root.attrib['id'] == 'x'
    assert root.text == 'ok'


def test_stdlib_preserves_mixed_text_and_children():
    root = parse_html('<div>Before <span>Inner</span> After</div>')
    assert root.tag == 'div'
    assert root.text == 'Before '
    assert len(root.children) == 1
    assert root.children[0].tag == 'span'
    assert root.children[0].text == 'Inner'
    assert root.children[0].tail.strip() == 'After'


def test_stdlib_handles_comments_and_void_tags():
    root = parse_html('<div><!--note--><br><img src="/a.png"></div>')
    tags = [child.tag for child in root.children]
    assert 'comment' in tags
    assert 'br' in tags
    assert 'img' in tags
    comment = next(c for c in root.children if c.is_comment)
    assert comment.text == 'note'


def test_element_from_html_uses_active_backend():
    set_html_parser_backend('stdlib')
    root = Element.from_html('<html><body><p id="a" class="x">Hi</p></body></html>')
    assert root.tag == 'html'
    found = root.querySelector('#a')
    assert found is not None
    assert found.content == 'Hi'


def test_unknown_backend_raises():
    with pytest.raises(ValueError):
        set_html_parser_backend('unknown')  # type: ignore[arg-type]


def test_lxml_backend_optional():
    try:
        import lxml  # noqa: F401
    except ImportError:
        with pytest.raises(ImportError):
            set_html_parser_backend('lxml')
            parse_html('<div>x</div>')
        return

    set_html_parser_backend('lxml')
    root = parse_html('<div id="z">ok</div>')
    assert root.tag == 'div'
    assert root.attrib['id'] == 'z'
    assert Element.from_html('<p>Hello</p>').tag == 'p'
