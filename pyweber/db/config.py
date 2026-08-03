"""Database configuration from env / config.toml."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class DatabaseSettings:
    url: str
    echo: bool = False
    pool_size: int = 5
    auto_commit: bool = False


def _truthy(value) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {'1', 'true', 'yes', 'on'}


def build_url_from_parts(
    db_type: str,
    *,
    name: str = '',
    username: str = '',
    password: str = '',
    host: str = 'localhost',
    port: str | int = '',
    dsn: str = '',
) -> str:
    """Build an async SQLAlchemy URL from discrete config fields."""
    if dsn:
        return str(dsn).strip()

    kind = (db_type or '').strip().lower()
    if kind in {'sqlite', 'aiosqlite'}:
        path = name or './app.db'
        if path == ':memory:':
            return 'sqlite+aiosqlite:///:memory:'
        return f'sqlite+aiosqlite:///{path.lstrip("/")}'

    userinfo = ''
    if username:
        from urllib.parse import quote_plus
        userinfo = quote_plus(str(username))
        if password:
            userinfo += f':{quote_plus(str(password))}'
        userinfo += '@'

    host = host or 'localhost'
    port_s = f':{port}' if port not in (None, '') else ''
    dbname = name or ''

    if kind in {'postgres', 'postgresql', 'asyncpg'}:
        return f'postgresql+asyncpg://{userinfo}{host}{port_s}/{dbname}'
    if kind in {'mysql', 'mariadb', 'aiomysql'}:
        return f'mysql+aiomysql://{userinfo}{host}{port_s}/{dbname}'
    if kind in {'mssql', 'sqlserver', 'aioodbc'}:
        # Driver name is environment-specific; document as experimental
        return f'mssql+aioodbc://{userinfo}{host}{port_s}/{dbname}?driver=ODBC+Driver+18+for+SQL+Server'

    raise ValueError(f'Unsupported database type: {db_type!r}')


def load_database_settings(
    *,
    url: str | None = None,
    echo: bool | None = None,
    pool_size: int | None = None,
    auto_commit: bool | None = None,
) -> DatabaseSettings:
    from pyweber.config.config import config

    resolved = (
        url
        or os.environ.get('PYWEBER_DATABASE_URL')
        or os.environ.get('DATABASE_URL')
        or config.get('database', 'url', default=None)
    )

    if not resolved:
        # Legacy nested section [database.database_1]
        nested = config.get('database', 'database_1', default=None) or {}
        if isinstance(nested, dict) and (nested.get('dsn') or nested.get('type')):
            resolved = build_url_from_parts(
                str(nested.get('type') or 'sqlite'),
                name=str(nested.get('name') or './app.db'),
                username=str(nested.get('username') or ''),
                password=str(nested.get('password') or ''),
                host=str(nested.get('host') or 'localhost'),
                port=nested.get('port') or '',
                dsn=str(nested.get('dsn') or ''),
            )

    if not resolved:
        resolved = 'sqlite+aiosqlite:///:memory:'

    if echo is None:
        echo = _truthy(
            os.environ.get('PYWEBER_DATABASE_ECHO')
            if os.environ.get('PYWEBER_DATABASE_ECHO') is not None
            else config.get('database', 'echo', default=False)
        )
    if pool_size is None:
        try:
            pool_size = int(
                os.environ.get('PYWEBER_DATABASE_POOL_SIZE')
                or config.get('database', 'pool_size', default=5)
                or 5
            )
        except (TypeError, ValueError):
            pool_size = 5
    if auto_commit is None:
        auto_commit = _truthy(config.get('database', 'auto_commit', default=False))

    return DatabaseSettings(
        url=str(resolved).strip(),
        echo=bool(echo),
        pool_size=max(1, int(pool_size)),
        auto_commit=bool(auto_commit),
    )
