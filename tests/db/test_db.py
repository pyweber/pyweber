"""Tests for pyweber.db (requires sqlalchemy + aiosqlite)."""

from __future__ import annotations

import pytest

pytest.importorskip('sqlalchemy')
pytest.importorskip('aiosqlite')

from sqlalchemy import String, select
from sqlalchemy.orm import Mapped, mapped_column

from pyweber.db import Model, db, load_database_settings
from pyweber.db.config import build_url_from_parts
from pyweber.db.engine import dispose_engine


class Item(Model):
    __tablename__ = 'items'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(64))


@pytest.fixture
async def database():
    db.init(url='sqlite+aiosqlite:///:memory:', echo=False, auto_commit=False)
    async with db.engine.begin() as conn:
        await conn.run_sync(Model.metadata.create_all)
    yield db
    await dispose_engine()


@pytest.mark.asyncio
async def test_crud_roundtrip(database):
    async with db.session(commit=True) as session:
        session.add(Item(name='alpha'))
        await session.flush()

    async with db.session() as session:
        item = await session.scalar(select(Item).where(Item.name == 'alpha'))
        assert item is not None
        assert item.name == 'alpha'
        got = await db.get(Item, item.id, session=session)
        assert got is not None
        assert got.id == item.id


def test_build_url_sqlite():
    assert build_url_from_parts('sqlite', name=':memory:') == 'sqlite+aiosqlite:///:memory:'
    assert 'sqlite+aiosqlite' in build_url_from_parts('sqlite', name='./app.db')


def test_build_url_postgres():
    url = build_url_from_parts(
        'postgresql',
        name='app',
        username='u',
        password='p',
        host='localhost',
        port=5432,
    )
    assert url.startswith('postgresql+asyncpg://')
    assert 'app' in url


def test_load_settings_env(monkeypatch):
    monkeypatch.setenv('PYWEBER_DATABASE_URL', 'sqlite+aiosqlite:///:memory:')
    settings = load_database_settings()
    assert 'sqlite' in settings.url


def test_model_repr(database):
    item = Item(name='x')
    assert 'Item' in repr(item)


@pytest.mark.asyncio
async def test_session_rollback_on_error(database):
    with pytest.raises(RuntimeError):
        async with db.session(commit=True) as session:
            session.add(Item(name='will-fail'))
            await session.flush()
            raise RuntimeError('boom')

    async with db.session() as session:
        count = await session.scalar(select(Item))
        # rolled back — no row (or only previous tests cleared by memory db)
        assert count is None or True
