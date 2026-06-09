import sys
from pathlib import Path
from types import ModuleType
from unittest.mock import MagicMock, patch

import pytest

from pyweber.models.create_app import CreatApp, DEFAULT_RELOAD_SKIP


@pytest.fixture
def project(tmp_path, monkeypatch):
    main = tmp_path / 'main.py'
    main.write_text('pass')
    monkeypatch.setattr(sys, 'argv', [str(main)])
    return tmp_path


class TestCreatAppExtended:
    def test_default_reload_skip(self):
        assert 'alembic' in DEFAULT_RELOAD_SKIP

    def test_is_reloadable_module(self, project):
        app = CreatApp(target=None, reload_skip_modules=list(DEFAULT_RELOAD_SKIP))
        assert app.is_reloadable_module('myapp.views') is True
        assert app.is_reloadable_module('alembic.runtime') is False

    def test_get_app_instances_from_module(self, project, monkeypatch):
        from pyweber.pyweber.pyweber import Pyweber

        fake = ModuleType('main')
        fake.app = Pyweber()
        creat = CreatApp(target=None)
        monkeypatch.setattr(creat, 'get_main_module', lambda: fake)
        assert creat.get_app_instances() is fake.app

    def test_get_app_instances_creates_default(self, project, monkeypatch):
        creat = CreatApp(target=None)
        monkeypatch.setattr(creat, 'get_main_module', lambda: ModuleType('main'))
        assert creat.get_app_instances() is not None

    def test_path_to_module(self, project):
        mod_file = project / 'pkg' / 'mod.py'
        mod_file.parent.mkdir(parents=True)
        mod_file.write_text('x = 1')
        app = CreatApp(target=None)
        assert app.path_to_module(str(mod_file)) == 'pkg.mod'

    def test_target_setter_rejects_non_callable(self):
        app = CreatApp(target=None)
        with pytest.raises(TypeError):
            app.target = 'not-callable'

    def test_target_none_allowed(self):
        app = CreatApp(target=None)
        assert app.target is None

    @patch.object(CreatApp, 'load_target')
    @patch('pyweber.models.create_app.Thread')
    def test_run_starts_reload_thread(self, mock_thread, mock_load, project):
        def target(app):
            app.add_route('/', template='hi', methods=['GET'])

        creat = CreatApp(target=target, reload_mode=True, port=8801, host='127.0.0.1')
        with patch.object(creat.http_server, 'run') as mock_http_run:
            creat.run()
        mock_load.assert_called_once()
        mock_thread.assert_called_once()
        mock_http_run.assert_called_once()

    def test_reset_reload_globals(self, project):
        from pyweber.connection.session import sessions, Session
        from unittest.mock import Mock

        sessions.add_session('s1', Session(template=Mock(), window=Mock(), session_id='s1', current_route='/'))
        CreatApp(target=None).reset_reload_globals()
        assert 's1' not in sessions.all_sessions
