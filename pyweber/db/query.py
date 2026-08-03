"""Light query helpers (escape hatch: use SQLAlchemy ``select`` directly)."""

from __future__ import annotations

from typing import Any, TypeVar

T = TypeVar('T')


async def get(model: type[T], ident: Any, *, session=None) -> T | None:
    """``session.get(model, ident)`` using the current or provided session."""
    from pyweber.db.session import get_current_session

    sess = session or get_current_session()
    if sess is None:
        raise RuntimeError('No database session. Use async with db.session() as session.')
    return await sess.get(model, ident)


async def scalars(statement, *, session=None):
    from pyweber.db.session import get_current_session

    sess = session or get_current_session()
    if sess is None:
        raise RuntimeError('No database session. Use async with db.session() as session.')
    return await sess.scalars(statement)
