from dataclasses import dataclass
from threading import Lock
from time import time
from uuid import uuid4

from pyweber.core.element import Element
from pyweber.core.template import Template

HANDOFF_TTL_SECONDS = 300
HANDOFF_META_NAME = 'pyweber-handoff'


@dataclass
class HandoffEntry:
    template: Template
    route: str
    created_at: float
    session_id: str | None = None


class TemplateHandoffRegistry:
    """One-shot HTTP → WS handoff of the **same** Template instance (move on consume).

    Storing a clone would type-erase subclasses and orphan ``self`` refs used by
    bound event handlers. The HTTP response and the future session share one object
    until ``consume`` moves it into the WebSocket session.
    """

    def __init__(self, ttl: int = HANDOFF_TTL_SECONDS):
        self._ttl = ttl
        self._entries: dict[str, HandoffEntry] = {}
        self._lock = Lock()

    def create(self, template: Template, route: str, session_id: str | None = None) -> str:
        token = str(uuid4())
        with self._lock:
            self._purge_expired()
            self._entries[token] = HandoffEntry(
                template=template,
                route=route,
                created_at=time(),
                session_id=session_id,
            )
        return token

    def consume(self, token: str, route: str, session_id: str | None = None) -> Template | None:
        """Move the template only after route, TTL and session id match.

        A wrong route or a different session leaves the entry in place.
        Entries created without ``session_id`` stay consumable by any caller
        (tests and older tokens).
        """
        if not token:
            return None

        with self._lock:
            entry = self._entries.get(token)
            if entry is None:
                return None
            if time() - entry.created_at > self._ttl:
                self._entries.pop(token, None)
                return None
            if entry.route != route:
                return None
            if entry.session_id and session_id != entry.session_id:
                return None
            self._entries.pop(token, None)

        return entry.template

    def clear(self):
        with self._lock:
            self._entries.clear()

    def _purge_expired(self):
        now = time()
        expired = [
            token for token, entry in self._entries.items()
            if now - entry.created_at > self._ttl
        ]
        for token in expired:
            del self._entries[token]


def inject_handoff_token(template: Template, token: str) -> None:
    head = template.head
    if not head:
        return

    for child in head.childs:
        if child.tag == 'meta' and child.get_attr('name') == HANDOFF_META_NAME:
            child.attrs['content'] = token
            return

    head.childs.append(
        Element(tag='meta', attrs={'name': HANDOFF_META_NAME, 'content': token})
    )


handoff_registry = TemplateHandoffRegistry()
