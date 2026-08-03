"""In-process reactive sessions with optional shared SessionStore backend."""

from __future__ import annotations

import asyncio
import logging
from time import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pyweber.core.template import Template
    from pyweber.core.window import Window

logger = logging.getLogger(__name__)


class Session:
    def __init__(self, template: 'Template', window: 'Window', session_id: str, current_route: str):
        self.template = template
        self.window = window
        self.session_id = session_id
        self.create_at = time()
        self.current_route = current_route
        self.old_template = template


class SessionManager:
    def __init__(self):
        self.__sessions: dict[str, Session] = {}
        self._store_configured = False

    def _ensure_store(self):
        if self._store_configured:
            return
        try:
            from pyweber.session_store import configure_session_store_from_config
            configure_session_store_from_config()
        except Exception as exc:
            logger.debug('session store config skipped: %s', exc)
        self._store_configured = True

    @property
    def sessions(self):
        return self.__sessions

    @property
    def length(self):
        return len(self.sessions)

    @property
    def all_sessions(self):
        return list(self.sessions.keys())

    def add_session(self, session_id: str, session: Session):
        assert isinstance(session, Session)
        self.sessions[session_id] = session
        self._schedule_persist(session)

    def remove_session(self, session_id: str):
        if session_id in self.sessions:
            del self.sessions[session_id]
        self._schedule_delete(session_id)

    def get_session(self, session_id: str):
        return self.sessions.get(session_id, None)

    async def aget_session(self, session_id: str) -> Session | None:
        """Local hit, otherwise hydrate from the configured SessionStore."""
        existing = self.get_session(session_id)
        if existing is not None:
            return existing

        self._ensure_store()
        from pyweber.session_store import get_session_store

        snapshot = await get_session_store().get(session_id)
        if snapshot is None:
            return None
        session = snapshot.to_session()
        self.sessions[session_id] = session
        return session

    async def apersist(self, session: Session) -> None:
        self._ensure_store()
        from pyweber.session_store import SessionSnapshot, default_ttl, get_session_store

        snap = SessionSnapshot.from_session(session)
        await get_session_store().set(session.session_id, snap, ttl=default_ttl())

    async def adelete(self, session_id: str) -> None:
        self._ensure_store()
        from pyweber.session_store import get_session_store

        await get_session_store().delete(session_id)

    def _schedule_persist(self, session: Session) -> None:
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self.apersist(session))
        except RuntimeError:
            try:
                asyncio.run(self.apersist(session))
            except Exception as exc:
                logger.debug('session persist failed: %s', exc)

    def _schedule_delete(self, session_id: str) -> None:
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self.adelete(session_id))
        except RuntimeError:
            try:
                asyncio.run(self.adelete(session_id))
            except Exception as exc:
                logger.debug('session delete failed: %s', exc)

    def __len__(self):
        return len(self.sessions)

    def __getitem__(self, session_id: str):
        return self.get_session(session_id=session_id)


sessions = SessionManager()
