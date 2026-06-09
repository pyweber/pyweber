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

    def test_reload_modules_reloads_all_project_modules(self, creat_app, tmp_path):
        mod_path = tmp_path / 'changed.py'
        mod_path.write_text('VALUE = 1\n', encoding='utf-8')
        other_path = tmp_path / 'other.py'
        other_path.write_text('VALUE = 2\n', encoding='utf-8')

        module = types.ModuleType('changed')
        module.VALUE = 1
        module.__file__ = str(mod_path)
        sys.modules['changed'] = module

        other = types.ModuleType('other')
        other.__file__ = str(other_path)
        sys.modules['other'] = other

        with patch.object(CreatApp, 'project_path', tmp_path), \
             patch.object(creat_app, 'path_to_module', return_value='changed'), \
             patch.object(creat_app, 'load_target'), \
             patch.object(creat_app, 'reset_reload_globals') as reset_mock, \
             patch('pyweber.models.create_app.reload') as reload_mock:
            creat_app.reload_modules(str(mod_path))
            assert reload_mock.call_count == 2
            reload_mock.assert_any_call(module)
            reload_mock.assert_any_call(other)
            reset_mock.assert_called_once()

        sys.modules.pop('changed', None)
        sys.modules.pop('other', None)

    def test_should_reload_module_skips_non_reloadable(self, creat_app):
        module = types.ModuleType('myapp.database.models')
        module.__file__ = str(creat_app.project_path / 'database' / 'models.py')
        assert creat_app._should_reload_module('myapp.database.models', module) is False

    def test_ordered_project_modules_deepest_first(self, creat_app, tmp_path):
        shallow = types.ModuleType('pkg')
        shallow.__file__ = str(tmp_path / 'pkg' / '__init__.py')
        deep = types.ModuleType('pkg.views')
        deep.__file__ = str(tmp_path / 'pkg' / 'views.py')
        sys.modules['pkg'] = shallow
        sys.modules['pkg.views'] = deep

        with patch.object(CreatApp, 'project_path', tmp_path):
            ordered = creat_app._ordered_project_modules()

        assert [name for name, _ in ordered] == ['pkg.views', 'pkg']

        sys.modules.pop('pkg', None)
        sys.modules.pop('pkg.views', None)
