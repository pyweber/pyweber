"""Async engine lifecycle."""

from __future__ import annotations

from typing import Any

from pyweber.db.config import DatabaseSettings, load_database_settings

_engine = None
_session_factory = None
_settings: DatabaseSettings | None = None


def _require_sqlalchemy():
    try:
        import sqlalchemy  # noqa: F401
        from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine
    except ImportError as exc:
        raise ImportError(
            "Database support requires the 'db' extra. "
            "Install with: pip install 'pyweber[db]' (and a driver extra, e.g. pyweber[db-sqlite])"
        ) from exc
    return AsyncEngine, async_sessionmaker, create_async_engine


def get_settings() -> DatabaseSettings | None:
    return _settings


def get_engine():
    return _engine


def get_session_factory():
    return _session_factory


def create_engine(settings: DatabaseSettings | None = None, **kwargs: Any):
    """Create (or replace) the process-wide async engine and session factory."""
    global _engine, _session_factory, _settings

    _, async_sessionmaker, create_async_engine = _require_sqlalchemy()
    settings = settings or load_database_settings(**{
        k: kwargs.pop(k) for k in ('url', 'echo', 'pool_size', 'auto_commit') if k in kwargs
    })
    _settings = settings

    engine_kwargs: dict[str, Any] = {'echo': settings.echo}
    # SQLite async does not use QueuePool the same way
    if not settings.url.startswith('sqlite'):
        engine_kwargs['pool_size'] = settings.pool_size

    engine_kwargs.update(kwargs)
    _engine = create_async_engine(settings.url, **engine_kwargs)
    _session_factory = async_sessionmaker(_engine, expire_on_commit=False)
    return _engine


async def dispose_engine() -> None:
    global _engine, _session_factory
    if _engine is not None:
        await _engine.dispose()
    _engine = None
    _session_factory = None
