"""Tests for session_store and SessionManager hydration."""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock

from pyweber.connection.session import Session, SessionManager, sessions
from pyweber.core.template import Template
from pyweber.core.window import Window
from pyweber.session_store import (
    MemorySessionStore,
    SessionSnapshot,
    configure_session_store,
    get_session_store,
)


@pytest.fixture
def isolated_sessions():
    """Use a fresh SessionManager + memory store for each test."""
    mgr = SessionManager()
    configure_session_store('memory')
    yield mgr
    configure_session_store('memory')


def _make_session(sid='s1', route='/'):
    tmpl = Template(template='<html><body><p>hi</p></body></html>', include_uuid=False)
    win = Window()
    win.session_id = sid
    return Session(template=tmpl, window=win, session_id=sid, current_route=route)


def test_snapshot_roundtrip():
    session = _make_session()
    snap = SessionSnapshot.from_session(session)
    assert snap.session_id == 's1'
    assert snap.current_route == '/'
    assert snap.template_html and 'hi' in snap.template_html

    restored = snap.to_session()
    assert restored.session_id == 's1'
    assert restored.current_route == '/'
    assert 'hi' in restored.template.build_html()


@pytest.mark.asyncio
async def test_memory_store():
    store = MemorySessionStore()
    snap = SessionSnapshot.from_session(_make_session('a'))
    await store.set('a', snap, ttl=60)
    assert await store.exists('a')
    got = await store.get('a')
    assert got is not None
    assert got.session_id == 'a'
    await store.delete('a')
    assert not await store.exists('a')


@pytest.mark.asyncio
async def test_session_manager_persist_and_hydrate(isolated_sessions):
    mgr = isolated_sessions
    session = _make_session('hydrate-1', route='/home')
    mgr.add_session('hydrate-1', session)
    await mgr.apersist(session)

    # Drop local cache, hydrate from store
    mgr.sessions.clear()
    assert mgr.get_session('hydrate-1') is None

    loaded = await mgr.aget_session('hydrate-1')
    assert loaded is not None
    assert loaded.current_route == '/home'
    assert mgr.get_session('hydrate-1') is loaded


@pytest.mark.asyncio
async def test_configure_redis_without_package(monkeypatch):
    import pyweber.session_store as ss

    real_import = __import__

    def fake_import(name, *args, **kwargs):
        if name == 'redis.asyncio' or name.startswith('redis'):
            raise ImportError('no redis')
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr('builtins.__import__', fake_import)
    with pytest.raises(ImportError, match='redis'):
        ss.RedisSessionStore('redis://localhost:6379/0')


@pytest.mark.asyncio
async def test_redis_store_with_fakeredis():
    redis = pytest.importorskip('redis')
    # Use a fake in-memory redis if available; otherwise skip when no server
    try:
        from redis.asyncio import Redis
        client = Redis.from_url('redis://localhost:6379/15')
        await client.ping()
    except Exception:
        pytest.skip('Redis server not available')

    configure_session_store('redis', redis_url='redis://localhost:6379/15', ttl=30)
    store = get_session_store()
    snap = SessionSnapshot.from_session(_make_session('redis-1'))
    await store.set('redis-1', snap)
    got = await store.get('redis-1')
    assert got is not None
    assert got.session_id == 'redis-1'
    await store.delete('redis-1')
    if hasattr(store, 'aclose'):
        await store.aclose()
    configure_session_store('memory')


def test_global_sessions_api():
    # smoke: module singleton still works
    assert hasattr(sessions, 'add_session')
    assert hasattr(sessions, 'aget_session')
