import sys
import types
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from pyweber.models.create_app import CreatApp, DEFAULT_RELOAD_SKIP
from pyweber.pyweber.pyweber import Pyweber
from pyweber.connection.session import sessions


@pytest.fixture
def creat_app(tmp_path):
    entry = tmp_path / 'main.py'
    entry.write_text('app = None\n', encoding='utf-8')

    def target(app):
        app.add_route(route='/', template='hi')

    with patch.object(sys, 'argv', [str(entry)]):
        ca = CreatApp(target=target, reload_skip_modules=['alembic', 'database'])
        yield ca


class TestCreatAppReload:
    def test_is_reloadable_module_skips_alembic(self, creat_app):
        assert creat_app.is_reloadable_module('myapp.database.models') is False
        assert creat_app.is_reloadable_module('myapp.routes.home') is True

    def test_default_skip_patterns(self):
        assert 'alembic' in DEFAULT_RELOAD_SKIP
        assert 'sqlalchemy' in DEFAULT_RELOAD_SKIP

    def test_reset_reload_globals_clears_sessions(self, creat_app):
        from pyweber.connection.session import Session
        from pyweber.core.window import Window

        sessions.add_session(
            'x',
            Session(template=Mock(), window=Window(), session_id='x', current_route='/'),
        )
        creat_app.reset_reload_globals()
        assert sessions.length == 0

    def test_path_to_module(self, creat_app, tmp_path):
        file_path = tmp_path / 'pkg' / 'routes.py'
        file_path.parent.mkdir()
        file_path.write_text('x=1', encoding='utf-8')
        with patch.object(CreatApp, 'project_path', tmp_path):
            assert creat_app.path_to_module(str(file_path)) == 'pkg.routes'

    def test_reload_modules_only_reloads_changed_module(self, creat_app, tmp_path):
        mod_path = tmp_path / 'changed.py'
        mod_path.write_text('VALUE = 1\n', encoding='utf-8')

        module = types.ModuleType('changed')
        module.VALUE = 1
        module.__file__ = str(mod_path)
        sys.modules['changed'] = module

        other = types.ModuleType('other')
        other.__file__ = str(tmp_path / 'other.py')
        sys.modules['other'] = other

        with patch.object(CreatApp, 'project_path', tmp_path), \
             patch.object(creat_app, 'path_to_module', return_value='changed'), \
             patch.object(creat_app, 'load_target'), \
             patch.object(creat_app, 'reset_reload_globals') as reset_mock, \
             patch('pyweber.models.create_app.reload') as reload_mock:
            creat_app.reload_modules(str(mod_path))
            reload_mock.assert_called_once_with(module)
            reset_mock.assert_called_once()

        sys.modules.pop('changed', None)
        sys.modules.pop('other', None)
