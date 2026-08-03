"""Request-scoped async session helpers."""

from __future__ import annotations

from contextlib import asynccontextmanager
from contextvars import ContextVar, Token
from typing import AsyncIterator

from pyweber.db.engine import get_session_factory, get_settings

_current_session: ContextVar[object | None] = ContextVar('pyweber_db_session', default=None)


def get_current_session():
    return _current_session.get()


def set_current_session(session) -> Token:
    return _current_session.set(session)


def reset_current_session(token: Token) -> None:
    _current_session.reset(token)


@asynccontextmanager
async def session_scope(*, commit: bool | None = None) -> AsyncIterator:
    """Open an ``AsyncSession``; commit on success when ``commit`` is true."""
    factory = get_session_factory()
    if factory is None:
        raise RuntimeError(
            'Database is not initialized. Call db.init_app(app) or db.init() first.'
        )

    settings = get_settings()
    do_commit = settings.auto_commit if commit is None and settings else bool(commit)

    session = factory()
    token = set_current_session(session)
    try:
        yield session
        if do_commit:
            await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        reset_current_session(token)
        await session.close()
