"""Tests for Alembic CLI helpers."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

pytest.importorskip('alembic')

from pyweber.db.cli import (
    configure_alembic_logging,
    handle_db_command,
    init_migrations,
    migrate,
)


def test_init_migrations(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    mig = init_migrations(tmp_path)
    assert (tmp_path / 'alembic.ini').exists()
    assert (mig / 'env.py').exists()
    assert (mig / 'script.py.mako').exists()
    assert (mig / 'versions').is_dir()
    assert 'pyweber db migrate' in (mig / 'README').read_text(encoding='utf-8')
    env = (mig / 'env.py').read_text(encoding='utf-8')
    assert 'configure_alembic_logging' in env
    assert 'fileConfig(config.config_file_name)' not in env
    ini = (tmp_path / 'alembic.ini').read_text(encoding='utf-8')
    assert 'propagate = 0' in ini
    # Root must not own the console handler — that captures server logs.
    root_block = ini.split('[logger_root]', 1)[1].split('[logger_', 1)[0]
    assert 'handlers = console' not in root_block


def test_configure_alembic_logging_preserves_existing_handlers(tmp_path: Path, capsys):
    ini = tmp_path / 'alembic.ini'
    init_migrations(tmp_path)

    root = logging.getLogger()
    saved_handlers = list(root.handlers)
    saved_level = root.level
    try:
        root.handlers.clear()
        stream = logging.StreamHandler()
        stream.setFormatter(logging.Formatter('APP %(message)s'))
        root.addHandler(stream)
        root.setLevel(logging.INFO)

        server = logging.getLogger('pyweber.test.server')
        server.disabled = False
        server.setLevel(logging.INFO)
        server.info('before-migrate')

        configure_alembic_logging(
            SimpleNamespace(config_file_name=str(ini), attributes={'configure_logger': True})
        )
        server.info('after-migrate')
    finally:
        root.handlers[:] = saved_handlers
        root.setLevel(saved_level)

    out = capsys.readouterr()
    combined = out.out + out.err
    assert 'before-migrate' in combined
    assert 'after-migrate' in combined
    assert server.disabled is False


def test_configure_alembic_logging_skips_when_flag_false(tmp_path: Path):
    init_migrations(tmp_path)
    with patch('pyweber.db.cli.fileConfig') as fc:
        configure_alembic_logging(
            SimpleNamespace(
                config_file_name=str(tmp_path / 'alembic.ini'),
                attributes={'configure_logger': False},
            )
        )
        fc.assert_not_called()


def test_configure_alembic_logging_applies_when_root_empty(tmp_path: Path):
    init_migrations(tmp_path)
    root = logging.getLogger()
    saved = list(root.handlers)
    try:
        root.handlers.clear()
        with patch('pyweber.db.cli.fileConfig') as fc:
            configure_alembic_logging(
                SimpleNamespace(
                    config_file_name=str(tmp_path / 'alembic.ini'),
                    attributes={},
                )
            )
            fc.assert_called_once()
            assert fc.call_args.kwargs.get('disable_existing_loggers') is False
    finally:
        root.handlers[:] = saved


def test_migrate_defaults_to_head():
    with patch('pyweber.db.cli.upgrade', return_value=0) as up:
        assert migrate() == 0
        up.assert_called_once_with('head')


def test_handle_db_migrate():
    args = argparse.Namespace(db_command='migrate', target='head')
    with patch('pyweber.db.cli.migrate', return_value=0) as mig:
        assert handle_db_command(args) == 0
        mig.assert_called_once_with('head')
