"""Tests for Alembic CLI helpers."""

from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip('alembic')

from pyweber.db.cli import init_migrations


def test_init_migrations(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    mig = init_migrations(tmp_path)
    assert (tmp_path / 'alembic.ini').exists()
    assert (mig / 'env.py').exists()
    assert (mig / 'script.py.mako').exists()
    assert (mig / 'versions').is_dir()
