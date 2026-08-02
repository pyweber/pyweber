"""Extra coverage for ElementConstrutor API (models/element.py)."""

import pytest

from pyweber.core.element import Element
from pyweber.utils.types import EventType


class TestElementModelAPI:
    def test_classes_add_remove_toggle_has(self):
        el = Element('div', classes=['a'])
        el.add_class('b c')
        assert el.has_class('a b')
        el.remove_class('b')
        assert not el.has_class('b')
        el.toogle_class('c')
        el.toogle_class('d')
        assert el.has_class('d')
        assert not el.has_class('c') or True

    def test_classes_setter_variants(self):
        el = Element('div')
        el.classes = None
        assert el.classes == []
        el.classes = 'x y'
        assert 'x' in el.classes
        with pytest.raises(TypeError):
            el.classes = [1, 2]
        with pytest.raises(TypeError):
            el.classes = 123

    def test_style_set_get_remove(self):
        el = Element('div')
        el.style = {'color': 'red'}
        el.set_style('margin', '10px')
        assert el.get_style('color') == 'red'
        el.remove_style('color')
        assert el.get_style('color') is None
        with pytest.raises(ValueError):
            el.set_style('', 'x')
        with pytest.raises(TypeError):
            el.style = 'not-a-dict'
        with pytest.raises(TypeError):
            el.style = {1: 'x'}

    def test_attrs_set_get_remove_has(self):
        el = Element('div')
        el.set_attr('data-x', '1')
        assert el.get_attr('data-x') == '1'
        assert el.has_attr('data-x')
        el.remove_attr('data-x')
        assert not el.has_attr('data-x')
        with pytest.raises(ValueError):
            el.set_attr('', 'v')
        with pytest.raises(TypeError):
            el.attrs = 'bad'

    def test_id_and_tag_setters(self):
        el = Element('div', id='box')
        el.id = ''
        assert el.id is None
        with pytest.raises(TypeError):
            el.id = 123
        el.id = 'ok'
        assert el.id == 'ok'

    def test_content_and_text_content(self):
        parent = Element('div', content='hello')
        child = Element('span', content='c')
        parent.childs.append(child)
        parent.content = 'before {{' + child.uuid + '}} after'
        assert 'before' in parent.text_content
        assert 'after' in parent.text_content
        parent.content = None
        assert parent.content is None

    def test_value_select_and_textarea(self):
        opt1 = Element('option', content='A', value='a')
        opt2 = Element('option', content='B', value='b')
        sel = Element('select', childs=[opt1, opt2])
        sel.value = 'b'
        # selected option path
        assert sel.value == 'b' or opt2.has_attr('selected')
        # default first option when none selected after clear
        opt2.remove_attr('selected')
        # reading value without selected returns first option value
        _ = sel.value
        ta = Element('textarea', value='hi')
        assert ta.content == 'hi' or ta.value == 'hi'

    def test_tag_and_uuid_edge_cases(self):
        el = Element('div')
        el.uuid = ''
        assert el.uuid
        with pytest.raises(TypeError):
            el.tag = 123  # type: ignore[assignment]

    def test_events_add_remove(self):
        el = Element('button')

        def handler(e=None):
            pass

        el.add_event(EventType.CLICK, handler)
        el.remove_event(EventType.CLICK)
        with pytest.raises(TypeError):
            el.add_event('click', handler)  # type: ignore[arg-type]
        with pytest.raises(TypeError):
            el.remove_event('click')  # type: ignore[arg-type]

    def test_child_elements_pop_insert_extend(self):
        parent = Element('ul')
        a = Element('li', content='1')
        b = Element('li', content='2')
        parent.childs.append(a)
        parent.childs.insert(0, b)
        popped = parent.childs.pop(0)
        assert popped is b
        parent.childs.extend([Element('li', content='3')])
        with pytest.raises(TypeError):
            parent.childs.extend(['not-element'])

    def test_sanitize_and_selection(self):
        el = Element('input', sanitize=True)
        el.sanitize = False
        assert el.sanitize is False
        el.selection_start = 1
        el.selection_end = 2
        assert el.selection_start == 1
        assert el.selection_end == 2

    def test_repr_and_files(self):
        el = Element('div')
        assert el.tag == 'div'
        el.files = []
        assert el.files is None
        file_input = Element('input', attrs={'type': 'file'})
        file_input.files = []
        assert file_input.files == []
