"""Static file resolution with path-traversal jail."""

from __future__ import annotations

import os

from pyweber.utils.loads import LoadStaticFiles
from pyweber.utils.security import safe_join
from pyweber.utils.types import StaticFilePath


class StaticFilesService:
    """Owns registered asset directories and safe path resolution."""

    def __init__(self, directories: set[str] | None = None):
        self.directories: set[str] = set(directories or ())

    def add(self, *directories: str) -> None:
        self.directories.update(directories)

    def roots(self) -> list[str]:
        roots = [os.path.realpath(str(StaticFilePath.favicon_path.value.parent))]
        for directory in self.directories:
            roots.append(os.path.realpath(directory))
        return roots

    def resolve_safe_path(self, path: str) -> str | None:
        if not path:
            return None
        roots = self.roots()
        abs_candidate = path
        if os.path.isfile(abs_candidate):
            real = os.path.realpath(abs_candidate)
            for root in roots:
                try:
                    if os.path.commonpath([root, real]) == root:
                        return real
                except ValueError:
                    continue
            return None

        stripped = path.replace('\\', '/').lstrip('/')
        framework_static = roots[0]

        if stripped.startswith('_pyweber/static/'):
            remainder = stripped[len('_pyweber/static/'):]
            joined = safe_join(framework_static, remainder)
            if joined and os.path.isfile(joined):
                return joined

        for directory in self.directories:
            name = directory.replace('\\', '/').strip('/')
            prefix = f'{name}/'
            if stripped == name or stripped.startswith(prefix):
                remainder = '' if stripped == name else stripped[len(name) + 1:]
                joined = safe_join(os.path.realpath(directory), remainder)
                if joined and os.path.isfile(joined):
                    return joined
        return None

    def is_static_file(self, route: str) -> bool:
        return self.resolve_safe_path(route) is not None

    def load(self, path: str):
        return LoadStaticFiles(path=path, allowed_roots=self.roots()).load

    def normalize_path(self, route: str) -> str:
        return os.path.normpath(path=route.removeprefix('/'))
