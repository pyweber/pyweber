"""Tests for Alembic CLI helpers."""

from __future__ import annotations

import argparse
from pathlib import Path
from unittest.mock import patch

import pytest

pytest.importorskip('alembic')

from pyweber.db.cli import handle_db_command, init_migrations, migrate


def test_init_migrations(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    mig = init_migrations(tmp_path)
    assert (tmp_path / 'alembic.ini').exists()
    assert (mig / 'env.py').exists()
    assert (mig / 'script.py.mako').exists()
    assert (mig / 'versions').is_dir()
    assert 'pyweber db migrate' in (mig / 'README').read_text(encoding='utf-8')


def test_migrate_defaults_to_head():
    with patch('pyweber.db.cli.upgrade', return_value=0) as up:
        assert migrate() == 0
        up.assert_called_once_with('head')


def test_handle_db_migrate():
    args = argparse.Namespace(db_command='migrate', target='head')
    with patch('pyweber.db.cli.migrate', return_value=0) as mig:
        assert handle_db_command(args) == 0
        mig.assert_called_once_with('head')
