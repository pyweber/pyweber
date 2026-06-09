"""Regressões de ordem: childs + content + placeholders {{}}."""

import re

from pyweber.core.element import Element


def _strip_ws(html: str) -> str:
    return re.sub(r'\s+', ' ', html).strip()


def test_content_and_child_preserves_inline_order():
    bold = Element('b', content='world')
    parent = Element('div', content='Hello ', childs=[bold])
    html = _strip_ws(parent.to_html())
    assert html.index('Hello') < html.index('<b') < html.index('world')


def test_kwargs_placeholder_slot_between_siblings():
    middle = Element('em', content='mid')
    left = Element('span', content='L')
    right = Element('span', content='R')
    parent = Element(
        'div',
        childs=[left, '{{slot}}', right],
        slot=middle,
    )
    html = _strip_ws(parent.to_html())
    assert html.index('L') < html.index('mid') < html.index('R')


def test_add_child_syncs_placeholder():
    parent = Element('div', content='Start ')
    child = Element('span', content='end')
    parent.add_child(child)
    assert '{{' + child.uuid + '}}' in parent.content
    html = _strip_ws(parent.to_html())
    assert html.index('Start') < html.index('end')


def test_from_html_preserves_mixed_text_and_children():
    root = Element.from_html('<div>Before <span>Inner</span> After</div>', include_uuid=False)
    html = _strip_ws(root.to_html())
    assert html.index('Before') < html.index('Inner') < html.index('After')


def test_to_html_does_not_duplicate_child_at_end():
    child = Element('i', content='x')
    parent = Element('div', content='{{' + child.uuid + '}} only', childs=[child])
    html = parent.to_html()
    assert html.count('<i') == 1


def test_content_replace_removes_orphan_children():
    """Regressão: badge.content = '1 pendente(s)' não deve duplicar filho antigo."""
    count = Element('span', content='1')
    badge = Element('span', classes=['badge'])
    badge.childs = [count]
    badge.content = '1 pendente(s)'
    html = _strip_ws(badge.to_html())
    assert html.count('>1<') == 0
    assert '1 pendente(s)' in html
    assert '1 1' not in html
    assert len(badge.childs) == 0


def test_content_with_placeholder_keeps_referenced_child():
    count = Element('span', content='1')
    badge = Element('span')
    badge.childs = [count]
    badge.content = f'{{{{{count.uuid}}}}} pendente(s)'
    html = _strip_ws(badge.to_html())
    assert 'pendente(s)' in html
    assert '>1<' in html
    assert len(badge.childs) == 1


def test_icon_not_duplicated_when_button_content_replaced():
    from pyweber.components.general import Icon

    icon = Icon('bi-check')
    button = Element('button', childs=[icon])
    button.content = 'Aprovar'
    html = button.to_html()
    assert html.count('<i') == 0
    assert 'Aprovar' in html


def test_icon_and_label_together_use_placeholders():
    from pyweber.components.general import Icon

    icon = Icon('bi-check')
    label = Element('span', content='Aprovar')
    button = Element('button', childs=[icon, label])
    html = _strip_ws(button.to_html())
    assert html.count('bi-check') == 1
    assert html.count('<i') == 1
    assert 'Aprovar' in html


def test_kwargs_icon_in_content_and_childs_not_duplicated():
    from pyweber.components.general import Icon

    icon = Icon('bi-folder-fill')
    heading = Element('h2', content='{{icon}} Requerimentos', childs=[icon], icon=icon)
    html = heading.to_html()
    assert html.count('bi-folder-fill') == 1

    save = Icon('bi-save')
    button = Element(
        'button',
        content='{{save}} Guardar Rascunho',
        childs=[save],
        save=save,
    )
    html = button.to_html()
    assert html.count('bi-save') == 1
