"""Textarea content + pretty-print indent regressions."""

from pyweber.components.general import TextArea
from pyweber.core.element import Element
from pyweber.models.element import normalize_preserved_inner_text


def test_element_textarea_keeps_constructor_content():
    ta = Element('textarea', content='hello world')
    assert ta.content == 'hello world'
    assert ta.value == 'hello world'
    html = ta.to_html()
    assert 'hello world' in html
    assert 'value="' not in html


def test_element_textarea_value_still_sets_content():
    ta = Element('textarea', content='ignored')
    ta.value = 'from-value'
    assert ta.content == 'from-value'
    assert ta.value == 'from-value'


def test_textarea_component_renders_body():
    area = TextArea(name='bio', content='hello', placeholder='type here')
    assert area.content == 'hello'
    html = area.to_html()
    assert 'hello' in html
    assert html.index('>') < html.index('hello') < html.index('</textarea>')


def test_textarea_multiline_to_html_does_not_indent_body():
    body = '**Maxixe**\n\n## Uma ponte\n- item'
    wrap = Element('div', childs=[Element('textarea', content=body)])
    html = wrap.to_html()
    inner = html.split('<textarea', 1)[1]
    inner = inner.split('>', 1)[1]
    inner = inner.rsplit('</textarea>', 1)[0]
    assert inner == body
    assert not inner.startswith(' ')
    assert not inner.startswith('\n')


def test_pre_multiline_to_html_does_not_indent_body():
    body = 'line1\n    indented'
    html = Element('pre', content=body).to_html()
    inner = html.split('<pre', 1)[1].split('>', 1)[1].rsplit('</pre>', 1)[0]
    assert inner == body


def test_from_html_pretty_printed_textarea_strips_indent():
    markup = (
        '<form>\n'
        '    <textarea>\n'
        '        **Maxixe**\n'
        '        ## titulo\n'
        '    </textarea>\n'
        '</form>'
    )
    root = Element.from_html(markup, include_uuid=False)
    ta = root.querySelector('textarea')
    assert ta is not None
    assert ta.content.startswith('**Maxixe**')
    assert not ta.content.startswith(' ')
    assert '## titulo' in ta.content


def test_from_html_inline_textarea_preserves_text():
    root = Element.from_html('<textarea>hello world</textarea>', include_uuid=False)
    assert root.content == 'hello world'


def test_textarea_roundtrip_keeps_markdown():
    body = '**Maxixe, 4 de Setembro**\n\n## Uma ponte\n- um\n- dois'
    html = Element('textarea', content=body).to_html(indent=8)
    parsed = Element.from_html(html, include_uuid=False)
    assert parsed.content == body


def test_textarea_clone_keeps_content():
    ta = Element('textarea', content='keep me')
    cloned = ta.clone
    assert cloned.content == 'keep me'
    assert cloned.value == 'keep me'


def test_normalize_preserved_inner_text_passthrough():
    assert normalize_preserved_inner_text(None) is None
    assert normalize_preserved_inner_text('hello') == 'hello'
    assert normalize_preserved_inner_text('\n    a\n    b\n') == 'a\nb'
