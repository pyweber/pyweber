import asyncio
from unittest.mock import AsyncMock, Mock, patch
from time import time

import pytest

from pyweber.connection.reload import ReloadHandler, ReloadServer


@pytest.fixture
def reload_server():
    return ReloadServer(
        ws_reload=AsyncMock(),
        http_reload=Mock(),
        extension_files=['.py', '.css', '.html'],
        ignore_reload_time=0,
        reload_cooldown=0,
    )


@pytest.fixture
def handler(reload_server):
    h = ReloadHandler(reload_server)
    h.start_server_time = 0
    return h


class TestReloadHandler:
    def test_get_hash_file_returns_sha256(self, handler, tmp_path):
        file_path = tmp_path / 'app.py'
        file_path.write_text('print("hello")', encoding='utf-8')
        digest = handler.get_hash_file(str(file_path))
        assert digest is not None
        assert len(digest) == 64

    def test_get_hash_file_missing_returns_none(self, handler):
        assert handler.get_hash_file('/nonexistent/file.py') is None

    @patch('pyweber.connection.reload.asyncio.run')
    @patch('pyweber.connection.reload.PrintLine')
    def test_on_modified_triggers_reload_on_real_change(self, _print, mock_run, handler, tmp_path):
        file_path = tmp_path / 'routes.py'
        file_path.write_text('x = 1', encoding='utf-8')
        path = handler._normalize_path(str(file_path))
        handler.hash_files[path] = handler.get_hash_file(path)
        file_path.write_text('x = 2', encoding='utf-8')

        event = Mock()
        event.is_directory = False
        event.src_path = str(file_path)

        handler.on_modified(event)

        handler.reload_server.http_reload.assert_called_once_with(path)
        mock_run.assert_called_once()

    @patch('pyweber.connection.reload.asyncio.run')
    @patch('pyweber.connection.reload.PrintLine')
    def test_css_change_does_not_restart_server(self, _print, mock_run, handler, tmp_path):
        file_path = tmp_path / 'style.css'
        file_path.write_text('body {}', encoding='utf-8')
        path = handler._normalize_path(str(file_path))
        handler.hash_files[path] = handler.get_hash_file(path)
        file_path.write_text('body { color: red; }', encoding='utf-8')

        event = Mock()
        event.is_directory = False
        event.src_path = str(file_path)

        handler.on_modified(event)

        handler.reload_server.http_reload.assert_not_called()
        mock_run.assert_called_once()

    @patch('pyweber.connection.reload.PrintLine')
    def test_on_modified_ignores_unknown_extension(self, _print, handler, tmp_path):
        file_path = tmp_path / 'notes.txt'
        file_path.write_text('x', encoding='utf-8')

        event = Mock()
        event.is_directory = False
        event.src_path = str(file_path)

        handler.on_modified(event)
        handler.reload_server.http_reload.assert_not_called()

    @patch('pyweber.connection.reload.PrintLine')
    def test_on_modified_skips_same_hash(self, _print, handler, tmp_path):
        file_path = tmp_path / 'app.py'
        file_path.write_text('stable', encoding='utf-8')
        path = handler._normalize_path(str(file_path))
        digest = handler.get_hash_file(path)
        handler.hash_files[path] = digest

        event = Mock()
        event.is_directory = False
        event.src_path = str(file_path)

        handler.on_modified(event)
        handler.reload_server.http_reload.assert_not_called()

    @patch('pyweber.connection.reload.PrintLine')
    def test_first_seen_file_establishes_baseline_without_reload(self, _print, handler, tmp_path):
        file_path = tmp_path / 'new.py'
        file_path.write_text('first', encoding='utf-8')
        path = handler._normalize_path(str(file_path))

        event = Mock()
        event.is_directory = False
        event.src_path = str(file_path)

        handler.on_modified(event)

        handler.reload_server.http_reload.assert_not_called()
        assert handler.hash_files[path] is not None
