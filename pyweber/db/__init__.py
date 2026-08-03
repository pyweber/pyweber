"""Flask-SQLAlchemy-style database facade for PyWeber."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pyweber.db.config import DatabaseSettings, load_database_settings
from pyweber.db.engine import (
    create_engine,
    dispose_engine,
    get_engine,
    get_session_factory,
    get_settings,
)
from pyweber.db.model import Model
from pyweber.db import query as query_helpers
from pyweber.db.session import get_current_session, session_scope

if TYPE_CHECKING:
    from pyweber.pyweber.pyweber import Pyweber


class Database:
    """Application database handle: ``db.init_app(app)`` then ``async with db.session()``."""

    Model = Model

    def __init__(self):
        self._app: Any = None
        self._middleware_registered = False

    @property
    def engine(self):
        return get_engine()

    @property
    def metadata(self):
        return Model.metadata

    @property
    def session_factory(self):
        return get_session_factory()

    @property
    def settings(self) -> DatabaseSettings | None:
        return get_settings()

    def init(
        self,
        url: str | None = None,
        *,
        echo: bool | None = None,
        pool_size: int | None = None,
        auto_commit: bool | None = None,
        **engine_kwargs: Any,
    ):
        """Initialize engine from URL / config (no app binding)."""
        settings = load_database_settings(
            url=url, echo=echo, pool_size=pool_size, auto_commit=auto_commit
        )
        create_engine(settings, **engine_kwargs)
        return self

    def init_app(
        self,
        app: Pyweber | None = None,
        *,
        url: str | None = None,
        echo: bool | None = None,
        pool_size: int | None = None,
        auto_commit: bool | None = None,
        auto_middleware: bool = False,
        **engine_kwargs: Any,
    ):
        """Bind to a PyWeber app and create the async engine."""
        self._app = app
        self.init(
            url=url,
            echo=echo,
            pool_size=pool_size,
            auto_commit=auto_commit,
            **engine_kwargs,
        )
        if auto_middleware and app is not None:
            self._register_middleware(app)
        return self

    def init_from_config(self, **kwargs: Any):
        return self.init(**kwargs)

    def session(self, *, commit: bool | None = None):
        """Async context manager yielding an ``AsyncSession``."""
        return session_scope(commit=commit)

    def get_session(self):
        """Return the ContextVar-bound session, if any."""
        return get_current_session()

    async def get(self, model, ident, *, session=None):
        return await query_helpers.get(model, ident, session=session)

    async def scalars(self, statement, *, session=None):
        return await query_helpers.scalars(statement, session=session)

    async def dispose(self):
        await dispose_engine()

    def _register_middleware(self, app: Pyweber):
        if self._middleware_registered:
            return

        @app.middleware()
        async def _db_session_middleware(request, call_next):
            async with self.session() as _session:
                return await call_next()

        self._middleware_registered = True


db = Database()

get = query_helpers.get
scalars = query_helpers.scalars

__all__ = [
    'Database',
    'db',
    'Model',
    'DatabaseSettings',
    'load_database_settings',
    'get',
    'scalars',
]
