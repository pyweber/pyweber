"""Alembic CLI helpers: ``pyweber db init|revision|upgrade|downgrade``."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ALEMBIC_INI = '''\
[alembic]
script_location = migrations
prepend_sys_path = .
version_path_separator = os

sqlalchemy.url = driver://user:pass@localhost/dbname

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
'''

ENV_PY = '''\
"""Alembic async environment for PyWeber."""
from __future__ import annotations

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

# Import your models so metadata is populated, e.g.:
# from models import User  # noqa: F401
from pyweber.db import Model
from pyweber.db.config import load_database_settings

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Model.metadata

settings = load_database_settings()
config.set_main_option('sqlalchemy.url', settings.url)


def run_migrations_offline() -> None:
    url = config.get_main_option('sqlalchemy.url')
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={'paramstyle': 'named'},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix='sqlalchemy.',
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
'''

SCRIPT_MAKO = '''\
"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
${imports if imports else ""}

# revision identifiers, used by Alembic.
revision: str = ${repr(up_revision)}
down_revision: Union[str, None] = ${repr(down_revision)}
branch_labels: Union[str, Sequence[str], None] = ${repr(branch_labels)}
depends_on: Union[str, Sequence[str], None] = ${repr(depends_on)}


def upgrade() -> None:
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    ${downgrades if downgrades else "pass"}
'''

README_MIGRATIONS = '''\
Generic single-database Alembic configuration for PyWeber (async).

1. Import your models in ``env.py`` so ``Model.metadata`` includes them.
2. ``pyweber db revision -m "message"``
3. ``pyweber db upgrade head``
'''


def _require_alembic():
    try:
        import alembic  # noqa: F401
    except ImportError as exc:
        raise SystemExit(
            "Alembic is required. Install with: pip install 'pyweber[db]'"
        ) from exc


def init_migrations(root: Path | None = None) -> Path:
    """Create alembic.ini + migrations/ scaffold in the project root."""
    _require_alembic()
    root = root or Path.cwd()
    ini = root / 'alembic.ini'
    mig = root / 'migrations'
    versions = mig / 'versions'

    if not ini.exists():
        ini.write_text(ALEMBIC_INI, encoding='utf-8')
    versions.mkdir(parents=True, exist_ok=True)
    (mig / 'env.py').write_text(ENV_PY, encoding='utf-8')
    (mig / 'script.py.mako').write_text(SCRIPT_MAKO, encoding='utf-8')
    (mig / 'README').write_text(README_MIGRATIONS, encoding='utf-8')
    return mig


def _alembic_cmd(*args: str) -> int:
    _require_alembic()
    return subprocess.call([sys.executable, '-m', 'alembic', *args])


def revision(message: str, *, autogenerate: bool = True) -> int:
    args = ['revision', '-m', message]
    if autogenerate:
        args.append('--autogenerate')
    return _alembic_cmd(*args)


def upgrade(target: str = 'head') -> int:
    return _alembic_cmd('upgrade', target)


def downgrade(target: str = '-1') -> int:
    return _alembic_cmd('downgrade', target)


def build_parser(subparsers) -> None:
    db_parser = subparsers.add_parser('db', help='Database / Alembic helpers (requires pyweber[db])')
    db_sub = db_parser.add_subparsers(dest='db_command')

    db_sub.add_parser('init', help='Create alembic.ini and migrations/ scaffold')

    rev = db_sub.add_parser('revision', help='Create a new Alembic revision')
    rev.add_argument('-m', '--message', required=True, help='Revision message')
    rev.add_argument(
        '--no-autogenerate',
        action='store_true',
        help='Do not pass --autogenerate to Alembic',
    )

    up = db_sub.add_parser('upgrade', help='Upgrade to a revision (default: head)')
    up.add_argument('target', nargs='?', default='head')

    down = db_sub.add_parser('downgrade', help='Downgrade to a revision (default: -1)')
    down.add_argument('target', nargs='?', default='-1')


def handle_db_command(args: argparse.Namespace) -> int:
    cmd = getattr(args, 'db_command', None)
    if cmd == 'init':
        path = init_migrations()
        print(f'Initialized Alembic migrations at {path}')
        return 0
    if cmd == 'revision':
        return revision(args.message, autogenerate=not args.no_autogenerate)
    if cmd == 'upgrade':
        return upgrade(args.target)
    if cmd == 'downgrade':
        return downgrade(args.target)
    print('Usage: pyweber db {init,revision,upgrade,downgrade}')
    return 1
