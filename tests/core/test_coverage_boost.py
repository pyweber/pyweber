"""Extra coverage for window APIs, element tree ops, and TaskManager."""

from __future__ import annotations

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from pyweber.core.element import Element
from pyweber.core.events import WindowEvents
from pyweber.core.window import (
    LocalStorage,
    Orientation,
    SessionStorage,
    Window,
    window,
)
from pyweber.models.context import reset_current_window, set_current_window
from pyweber.models.task_manager import TaskManager
from pyweber.utils.types import EventType, OrientationType, WindowEventType


class TestWindowApiCoverage:
    def test_repr_and_orientation_on_change(self):
        w = Window()
        assert 'Window(' in repr(w)
        ori = Orientation(0, OrientationType.LANDSCAPE_PRIMARY, None)
        assert ori.on_change is None
        ori.on_change = lambda: None
        assert callable(ori.on_change)
        with pytest.raises(TypeError):
            ori.on_change = 'nope'

    def test_events_setter_type_error(self):
        w = Window()
        with pytest.raises(TypeError):
            w.events = object()

    def test_add_remove_event_type_errors(self):
        w = Window()
        with pytest.raises(TypeError):
            w.add_event('load', lambda e: None)
        with pytest.raises(TypeError):
            w.add_event(WindowEventType.LOAD, 'nope')
        with pytest.raises(TypeError):
            w.remove_event('load')

    def test_alert_open_close_scroll_atob(self):
        w = Window()
        with patch.object(w, '__send__') as send:
            w.alert('hi')
            send.assert_called_with(data={'alert': 'hi'})
            w.close()
            send.assert_called_with(data={'close': True})
            w.scroll_to(1, 2)
            assert send.call_args.kwargs['data']['scroll_to']['x'] == 1
            w.open('/safe')
            assert 'open' in send.call_args.kwargs['data']
            w.clear_interval('x')
            assert 'clear_interval' in send.call_args.kwargs['data']
            w.cancel_animation_frame('f')
            assert 'cancel_animation_frame' in send.call_args.kwargs['data']
        assert w.atob(w.btoa('abc')) == 'abc'
        with pytest.raises(TypeError):
            w._register_timer('nope')

    @pytest.mark.asyncio
    async def test_confirm_and_prompt(self):
        w = Window()
        w.session_id = 'c1'
        ws = MagicMock()
        ws.send_message = AsyncMock()
        ws.get_window_response = AsyncMock(
            return_value={'confirm_result': 'yes', 'confirm_id': 'cid'}
        )
        w._Window__ws = ws
        conf = await w.confirm('ok?', timeout=1)
        assert conf.result == 'yes'

        ws.get_window_response = AsyncMock(
            return_value={'prompt_result': 'ans', 'prompt_id': 'pid'}
        )
        prompt = await w.prompt('q?', default='d', timeout=1)
        assert prompt.result == 'ans'

    def test_proxy_repr(self):
        w = Window()
        token = set_current_window(w)
        try:
            assert 'Window(' in repr(window)
        finally:
            reset_current_window(token)
        assert 'no active' in repr(window)

    @patch('asyncio.run', return_value=None)
    def test_local_and_session_storage(self, mock_run):
        ws = MagicMock()
        ws.send_message = AsyncMock(return_value=None)
        ls = LocalStorage({'a': 1}, 's1', ws)
        ls.set('b', {'n': 1})
        assert json.loads(ls.data['b']) == {'n': 1}
        ls.clear()
        assert ls.data == {}
        ls.set('c', 'v')
        assert ls.pop('c') == 'v'
        assert ls.pop('missing') is None

        ss = SessionStorage({}, 's1', ws)
        ss.set('k', 'v')
        ss.clear()
        ss.set('k2', 'v2')
        assert ss.pop('k2') == 'v2'


class TestElementTreeCoverage:
    def test_parent_type_error_and_child_ops(self):
        parent = Element('div')
        child = Element('span', content='x')
        parent.childs = [child]
        assert child.parent is parent
        assert child.index == 0
        assert parent.first_child() is child
        assert parent.last_child() is child
        with pytest.raises(TypeError):
            child.parent = 'nope'
        with pytest.raises(TypeError):
            parent.childs = 'nope'
        with pytest.raises(TypeError):
            parent.add_child('nope')
        sibling = Element('p', content='y')
        parent.add_child(sibling)
        assert child.next_child() is sibling
        assert sibling.previous_child() is child
        sibling.remove()
        assert sibling.parent is None
        with pytest.raises(IndexError):
            parent.remove_child(sibling)
        with pytest.raises(TypeError):
            parent.pop_child('0')
        alone = Element('i')
        assert alone.first_child() is None
        assert alone.last_child() is None
        assert alone.previous_child() is None
        assert alone.next_child() is None
        assert alone.index is None

    def test_focus_blur_select_click_scroll(self):
        el = Element('input')
        el.selection_start = 0
        el.selection_end = 0
        with patch.object(el, '_Element__set_element_methods') as m:
            el.focus()
            el.blur()
            el.select()
            el.click()
            el.scroll_into_view()
            el.set_selection_range(0, 1)
            assert m.call_count >= 5

    def test_get_elements_search_modes(self):
        root = Element(
            'div',
            classes=['foo', 'bar'],
            attrs={'data-x': '1', 'title': 'hello'},
            childs=[
                Element('span', classes=['item-a'], content='alpha'),
                Element('span', classes=['item-b'], content='beta'),
            ],
        )
        assert root.getElements(by='classes', value='foo bar')
        assert root.getElements(by='classes', value='item', search_mode='contains')
        assert root.getElements(by='classes', value='^item', search_mode='regex')
        assert root.getElements(by='classes', value='item', search_mode='startswith')
        assert root.getElements(by='classes', value='-a', search_mode='endswith')
        assert root.getElements(by='attrs', value='data-x=1')
        assert root.getElements(by='attrs', value='data-x')
        assert root.getElements(by='attrs', value='hello', search_mode='contains')
        assert root.getElements(by='attrs', value='data', search_mode='startswith')
        assert root.getElements(by='attrs', value='x', search_mode='endswith')
        assert root.getElements(by='attrs', value='title', search_mode='regex')
        assert root.getElements(by='content', value='alp', search_mode='contains')
        assert root.getElements(by='content', value='^alp', search_mode='regex')
        assert root.getElements(by='content', value='al', search_mode='startswith')
        assert root.getElements(by='content', value='ha', search_mode='endswith')


class TestTaskManagerCoverage:
    @pytest.mark.asyncio
    async def test_cancel_async_and_errors(self):
        manager = TaskManager()
        started = asyncio.Event()
        release = asyncio.Event()

        async def long_handler(e):
            started.set()
            await release.wait()

        eh = MagicMock()
        eh.window = Window()
        task = asyncio.create_task(
            manager.create_task_async('s1', 'e1', long_handler, eh)
        )
        await started.wait()
        cancelled = await manager.cancel_all_tasks_async('s1')
        assert cancelled >= 1
        release.set()
        await asyncio.gather(task, return_exceptions=True)

        async def boom(e):
            raise ValueError('boom')

        with pytest.raises(ValueError):
            await manager.create_task_async('s2', 'e2', boom, eh)

        await manager.cancel_all_async()
        manager.cancel_session_handlers('missing')
        manager.shutdown()

    def test_sync_handler_error_and_duplicate(self):
        manager = TaskManager()
        eh = MagicMock()
        eh.window = Window()

        def boom(e):
            raise RuntimeError('sync-fail')

        assert manager.create_task('s3', 'e3', boom, eh) is True
        manager.executor.shutdown(wait=True)

        def hang(e):
            import time
            time.sleep(0.3)

        manager2 = TaskManager()
        assert manager2.create_task('s4', 'e4', hang, eh) is True
        assert manager2.create_task('s4', 'e4', hang, eh) is False
        manager2.cancel_session_handlers('s4')
        manager2.shutdown()
