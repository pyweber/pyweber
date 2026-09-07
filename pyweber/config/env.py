"""Resolve ``${VAR}`` / ``${VAR:-default}`` in config values and load ``.env`` files.

Process environment always wins over ``.env``. ``config.save()`` must dump the
unresolved tree so secrets never land in ``config.toml``.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any, Mapping

_ENV_REF = re.compile(r'\$\{([A-Za-z_][A-Za-z0-9_]*)(?::-([^}]*))?\}')
_FULL_REF = re.compile(r'^\$\{[A-Za-z_][A-Za-z0-9_]*(?::-([^}]*))?\}$')
_ENV_KEY = re.compile(r'^[A-Za-z_][A-Za-z0-9_]*$')
_DOLLAR = '\x00'


def parse_dotenv(content: str) -> dict[str, str]:
    """Parse a subset of dotenv syntax: ``KEY=value``, optional ``export``, quotes, comments."""
    result: dict[str, str] = {}
    for raw in content.splitlines():
        line = raw.strip()
        if not line or line.startswith('#'):
            continue
        if line.startswith('export '):
            line = line[7:].strip()
        if '=' not in line:
            continue
        key, _, value = line.partition('=')
        key = key.strip()
        if not _ENV_KEY.match(key):
            continue
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
            value = value[1:-1]
        result[key] = value
    return result


def apply_dotenv(path: Path | str, *, protected: set[str] | None = None) -> None:
    """Load ``path`` into ``os.environ`` without overriding ``protected`` keys (process env)."""
    file = Path(path)
    if not file.is_file():
        return
    try:
        parsed = parse_dotenv(file.read_text(encoding='utf-8'))
    except OSError:
        return
    skip = protected if protected is not None else set()
    for key, value in parsed.items():
        if key in skip:
            continue
        os.environ[key] = value


def dotenv_candidates(config_file: Path | str | None = None) -> list[Path]:
    """``.env`` search paths, lowest priority first.

    ``PYWEBER_ENV_FILE`` (if set) is last so it wins among files. Process env
    is applied separately and always wins.
    """
    seen: set[Path] = set()
    ordered: list[Path] = []

    def add(path: Path) -> None:
        try:
            resolved = path.resolve()
        except OSError:
            resolved = path
        if resolved in seen:
            return
        seen.add(resolved)
        ordered.append(path)

    if config_file:
        cfg = Path(config_file)
        add(cfg.parent / '.env')
        add(cfg.parent.parent / '.env')
    add(Path.cwd() / '.env')
    explicit = os.environ.get('PYWEBER_ENV_FILE')
    if explicit:
        add(Path(explicit))
    return ordered


def load_dotenv(config_file: Path | str | None = None) -> None:
    """Fill missing ``os.environ`` keys from discovered ``.env`` files."""
    protected = set(os.environ)
    for path in dotenv_candidates(config_file):
        apply_dotenv(path, protected=protected)


def interpolate_string(text: str, environ: Mapping[str, str] | None = None) -> str:
    """Replace ``${VAR}`` and ``${VAR:-default}``. ``$$`` becomes a literal ``$``."""
    if not text or ('${' not in text and '$$' not in text):
        return text
    env = os.environ if environ is None else environ

    def replace(match: re.Match[str]) -> str:
        name, default = match.group(1), match.group(2)
        current = env.get(name)
        if current:
            return current
        if default is not None:
            return default
        return current if current is not None else ''

    expanded = text.replace('$$', _DOLLAR)
    expanded = _ENV_REF.sub(replace, expanded)
    return expanded.replace(_DOLLAR, '$')


def coerce_env_value(text: str) -> Any:
    """Cast a fully substituted env value to bool/int when it looks like one."""
    stripped = text.strip()
    lower = stripped.lower()
    if lower in {'true', 'yes', 'on'}:
        return True
    if lower in {'false', 'no', 'off'}:
        return False
    if stripped.isdigit() or (stripped.startswith('-') and stripped[1:].isdigit()):
        return int(stripped)
    return text


def resolve_config_value(value: Any, environ: Mapping[str, str] | None = None) -> Any:
    """Walk config values, interpolating strings and wrapping dicts."""
    if isinstance(value, dict):
        return EnvConfigView(value, environ)
    if isinstance(value, list):
        return [resolve_config_value(item, environ) for item in value]
    if isinstance(value, str):
        resolved = interpolate_string(value, environ)
        if _FULL_REF.match(value.strip()):
            return coerce_env_value(resolved)
        return resolved
    return value


class EnvConfigView(dict):
    """Live mapping: reads interpolate from env, writes keep the raw ``${VAR}`` text."""

    def __init__(self, data: dict, environ: Mapping[str, str] | None = None):
        super().__init__()
        self._data = data
        self._environ = environ

    def __getitem__(self, key):
        return resolve_config_value(self._data[key], self._environ)

    def __setitem__(self, key, value):
        self._data[key] = value

    def __delitem__(self, key):
        del self._data[key]

    def __contains__(self, key):
        return key in self._data

    def __iter__(self):
        return iter(self._data)

    def __len__(self):
        return len(self._data)

    def __repr__(self):
        return repr({key: resolve_config_value(val, self._environ) for key, val in self._data.items()})

    def get(self, key, default=None):
        if key not in self._data:
            return default
        return resolve_config_value(self._data[key], self._environ)

    def keys(self):
        return self._data.keys()

    def items(self):
        return [
            (key, resolve_config_value(val, self._environ))
            for key, val in self._data.items()
        ]

    def values(self):
        return [resolve_config_value(val, self._environ) for val in self._data.values()]

    def setdefault(self, key, default=None):
        if key not in self._data:
            self._data[key] = {} if default is None else default
        return resolve_config_value(self._data[key], self._environ)

    def pop(self, key, *args):
        if key not in self._data:
            return self._data.pop(key, *args)
        return resolve_config_value(self._data.pop(key), self._environ)

    def update(self, other=None, **kwargs):
        if other:
            self._data.update(dict(other))
        if kwargs:
            self._data.update(kwargs)

    def clear(self):
        self._data.clear()
