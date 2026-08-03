"""Pluggable reactive session stores (memory / Redis)."""

from __future__ import annotations

import json
import os
import time
from dataclasses import asdict, dataclass
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from pyweber.core.template import Template
    from pyweber.core.window import Window
    from pyweber.connection.session import Session


@dataclass
class SessionSnapshot:
    """Serializable session payload for shared backends (e.g. Redis)."""

    session_id: str
    current_route: str
    create_at: float
    template_html: str | None = None
    include_uuid: bool = True

    def to_json(self) -> str:
        return json.dumps(asdict(self))

    @classmethod
    def from_json(cls, raw: str | bytes) -> SessionSnapshot:
        data = json.loads(raw)
        return cls(**data)

    @classmethod
    def from_session(cls, session: Session) -> SessionSnapshot:
        html = None
        include_uuid = True
        template = getattr(session, 'template', None)
        if template is not None:
            include_uuid = bool(getattr(template, 'include_uuid', True))
            try:
                html = template.build_html() if hasattr(template, 'build_html') else str(template)
            except Exception:
                html = str(template)
        return cls(
            session_id=session.session_id,
            current_route=session.current_route,
            create_at=float(getattr(session, 'create_at', time.time())),
            template_html=html,
            include_uuid=include_uuid,
        )

    def to_session(self) -> Session:
        from pyweber.connection.session import Session
        from pyweber.core.template import Template
        from pyweber.core.window import Window

        template = Template(
            template=self.template_html or '<html><body></body></html>',
            include_uuid=self.include_uuid,
        )
        window = Window()
        window.session_id = self.session_id
        session = Session(
            template=template,
            window=window,
            session_id=self.session_id,
            current_route=self.current_route,
        )
        session.create_at = self.create_at
        session.old_template = template
        return session


class SessionStore(Protocol):
    async def get(self, session_id: str) -> SessionSnapshot | None: ...

    async def set(
        self,
        session_id: str,
        snapshot: SessionSnapshot,
        ttl: int | None = None,
    ) -> None: ...

    async def delete(self, session_id: str) -> None: ...

    async def exists(self, session_id: str) -> bool: ...


class MemorySessionStore:
    """In-process snapshot store (default)."""

    def __init__(self):
        self._data: dict[str, SessionSnapshot] = {}

    async def get(self, session_id: str) -> SessionSnapshot | None:
        return self._data.get(session_id)

    async def set(
        self,
        session_id: str,
        snapshot: SessionSnapshot,
        ttl: int | None = None,
    ) -> None:
        self._data[session_id] = snapshot

    async def delete(self, session_id: str) -> None:
        self._data.pop(session_id, None)

    async def exists(self, session_id: str) -> bool:
        return session_id in self._data

    def clear(self) -> None:
        self._data.clear()


class RedisSessionStore:
    """Redis-backed snapshot store (requires ``pyweber[redis]``)."""

    def __init__(
        self,
        url: str,
        *,
        prefix: str = 'pyweber:session:',
        ttl: int = 3600,
    ):
        try:
            from redis.asyncio import Redis
        except ImportError as exc:
            raise ImportError(
                "Redis session backend requires the 'redis' extra. "
                "Install with: pip install 'pyweber[redis]'"
            ) from exc
        self._redis = Redis.from_url(url, decode_responses=True)
        self.prefix = prefix
        self.ttl = ttl

    def _key(self, session_id: str) -> str:
        return f'{self.prefix}{session_id}'

    async def get(self, session_id: str) -> SessionSnapshot | None:
        raw = await self._redis.get(self._key(session_id))
        if not raw:
            return None
        return SessionSnapshot.from_json(raw)

    async def set(
        self,
        session_id: str,
        snapshot: SessionSnapshot,
        ttl: int | None = None,
    ) -> None:
        expire = self.ttl if ttl is None else ttl
        await self._redis.set(self._key(session_id), snapshot.to_json(), ex=expire)

    async def delete(self, session_id: str) -> None:
        await self._redis.delete(self._key(session_id))

    async def exists(self, session_id: str) -> bool:
        return bool(await self._redis.exists(self._key(session_id)))

    async def aclose(self) -> None:
        await self._redis.aclose()


_store: SessionStore = MemorySessionStore()
_ttl: int = 3600


def get_session_store() -> SessionStore:
    return _store


def configure_session_store(
    backend: str = 'memory',
    *,
    redis_url: str | None = None,
    ttl: int = 3600,
    key_prefix: str = 'pyweber:session:',
) -> SessionStore:
    """Configure the process-wide session store backend."""
    global _store, _ttl
    _ttl = int(ttl)
    kind = (backend or 'memory').strip().lower()
    if kind in {'', 'memory', 'mem', 'local'}:
        _store = MemorySessionStore()
    elif kind == 'redis':
        url = (
            redis_url
            or os.environ.get('PYWEBER_REDIS_URL')
            or os.environ.get('REDIS_URL')
            or 'redis://localhost:6379/0'
        )
        _store = RedisSessionStore(url, prefix=key_prefix, ttl=_ttl)
    else:
        raise ValueError(f'Unknown session backend: {backend!r}')
    return _store


def configure_session_store_from_config() -> SessionStore:
    from pyweber.config.config import config

    backend = (
        os.environ.get('PYWEBER_SESSION_BACKEND')
        or config.get('session', 'backend', default='memory')
        or 'memory'
    )
    redis_url = (
        os.environ.get('PYWEBER_REDIS_URL')
        or os.environ.get('REDIS_URL')
        or config.get('session', 'redis_url', default=None)
    )
    try:
        ttl = int(
            os.environ.get('PYWEBER_SESSION_TIMEOUT')
            or config.get('session', 'timeout', default=3600)
            or 3600
        )
    except (TypeError, ValueError):
        ttl = 3600
    prefix = config.get('session', 'key_prefix', default='pyweber:session:') or 'pyweber:session:'
    return configure_session_store(
        str(backend),
        redis_url=redis_url,
        ttl=ttl,
        key_prefix=str(prefix),
    )


def default_ttl() -> int:
    return _ttl


__all__ = [
    'SessionSnapshot',
    'SessionStore',
    'MemorySessionStore',
    'RedisSessionStore',
    'get_session_store',
    'configure_session_store',
    'configure_session_store_from_config',
    'default_ttl',
]
