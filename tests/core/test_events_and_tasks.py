import asyncio
from unittest.mock import Mock

import pytest

from pyweber.core.window import Window
from pyweber.core.events import EventData, EventConstrutor, EventHandler
from pyweber.models.context import get_current_window
from pyweber.models.task_manager import TaskManager


@pytest.fixture
def event_handler_setup():
    template = Mock()
    element = Mock()
    element.events = Mock()
    element.events.__dict__ = {}
    template.getElement = Mock(return_value=element)

    session = Mock()
    session.session_id = 'sess-1'
    session.template = template
    win = Window()
    win.session_id = 'sess-1'
    session.window = win

    ws = Mock()
    app = Mock()

    return session, template, ws, app, win


class TestEventData:
    def test_mouse_fields(self):
        data = EventData({'clientX': 10, 'clientY': 20, 'button': 0})
        assert data.clientX == 10
        assert data.clientY == 20
        assert data.button == 0

    def test_keyboard_fields(self):
        data = EventData({'key': 'Enter', 'ctrlKey': True})
        assert data.key == 'Enter'
        assert data.ctrl_key is True


class TestEventConstrutor:
    def test_build_event(self, event_handler_setup):
        session, template, ws, app, win = event_handler_setup
        constructor = EventConstrutor(
            target_id='uuid-1',
            current_target_id='uuid-1',
            app=app,
            ws=ws,
            session=session,
            route='/',
            event_data={'key': 'a'},
            event_type='keydown',
        )
        handler = constructor.build_event()
        assert isinstance(handler, EventHandler)
        assert handler.session is session
        assert handler.window is win


class TestTaskManager:
    @pytest.mark.asyncio
    async def test_async_handler_sets_window_context(self, event_handler_setup):
        session, _, _, _, win = event_handler_setup
        manager = TaskManager()
        seen = []

        async def handler(e):
            seen.append(get_current_window() is e.window)

        eh = Mock()
        eh.window = win

        await manager.create_task_async('sess-1', 'evt-1', handler, eh)
        assert seen == [True]
        manager.shutdown()

    def test_sync_handler_sets_window_context(self, event_handler_setup):
        session, _, _, _, win = event_handler_setup
        manager = TaskManager()
        seen = []

        def handler(e):
            seen.append(get_current_window() is e.window)

        eh = Mock()
        eh.window = win

        created = manager.create_task('sess-1', 'evt-1', handler, eh)
        assert created is True
        manager.executor.shutdown(wait=True)
        assert seen == [True]

    @pytest.mark.asyncio
    async def test_duplicate_async_task_not_created(self, event_handler_setup):
        _, _, _, _, win = event_handler_setup
        manager = TaskManager()
        counter = {'n': 0}

        async def slow_handler(e):
            counter['n'] += 1
            await asyncio.sleep(0.05)

        eh = Mock()
        eh.window = win

        task1 = asyncio.create_task(
            manager.create_task_async('sess-1', 'dup', slow_handler, eh)
        )
        await asyncio.sleep(0)
        result = await manager.create_task_async('sess-1', 'dup', slow_handler, eh)
        assert result == 'dup'
        await task1
        assert counter['n'] == 1
        manager.shutdown()
