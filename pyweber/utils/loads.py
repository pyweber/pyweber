import os
import sys
import toml
from pathlib import Path
from pyweber.utils.types import ContentTypes, StaticFilePath

class LoadStaticFiles:

    def __init__(self, path: str, allowed_roots: list[str] | None = None):
        argv0 = os.path.abspath(sys.argv[0])
        if os.path.isfile(argv0):
            self.__script_dir = os.path.dirname(argv0)
        else:
            self.__script_dir = str(Path.cwd())

        self.__allowed_roots = [os.path.realpath(r) for r in (allowed_roots or []) if r]

        if sys.platform == 'win32':
            self.__path = path[1:] if path.startswith('/') else path
        else:
            self.__path = path
            self.__path_2 = str(Path(self.__script_dir) / path.removeprefix('/'))

        # Preserve original for absolute / already-resolved paths
        self.__original_path = path

    def _is_allowed(self, candidate: str) -> bool:
        if not self.__allowed_roots:
            return True
        real = os.path.realpath(candidate)
        for root in self.__allowed_roots:
            try:
                if os.path.commonpath([root, real]) == root:
                    return True
            except ValueError:
                continue
        return False

    @property
    def load(self) -> str | bytes:
        extension = self.__path.split('.')[-1].strip()
        mode, encoding = 'r', 'utf-8'

        try:
            if ContentTypes.content_list().index(extension) >= ContentTypes.content_list().index('png'):
                mode, encoding = 'rb', None
        except ValueError:
            pass

        candidates = [
            self.__original_path,
            self.__path,
            self.__path.removeprefix('/'),
            getattr(self, '_LoadStaticFiles__path_2', None)
        ]

        for candidate in candidates:
            if candidate and os.path.exists(candidate) and self._is_allowed(candidate):
                return self.__read_file(path=candidate, mode=mode, encoding=encoding)

        raise FileNotFoundError('File not found, please ensure that path is correct')

    def __read_file(self, path: str, mode: str, encoding: str):
        with open(path, mode=mode, encoding=encoding) as file:
            return file.read()

class StaticTemplates:

    @staticmethod
    def BASE_HTML() -> str:
        return LoadStaticFiles(
            path=str(StaticFilePath.html_base.value)
        ).load

    @staticmethod
    def BASE_CSS() -> str:
        return LoadStaticFiles(
            path=str(StaticFilePath.css_base.value)
        ).load

    @staticmethod
    def BASE_MAIN() -> str:
        return LoadStaticFiles(
            path=str(StaticFilePath.main_base.value)
        ).load

    @staticmethod
    def JS_STATIC() -> str:
        return LoadStaticFiles(
            path=str(StaticFilePath.js_base.value)
        ).load

    @staticmethod
    def PAGE_NOT_FOUND() -> str:
        return LoadStaticFiles(
            path=str(StaticFilePath.html_404.value)
        ).load

    @staticmethod
    def PAGE_UNAUTHORIZED() -> str:
        return LoadStaticFiles(
            path=str(StaticFilePath.html_401.value)
        ).load

    @staticmethod
    def PAGE_SERVER_ERROR() -> str:
        return LoadStaticFiles(
            path=str(StaticFilePath.html_500.value)
        ).load

    @staticmethod
    def FAVICON() -> bytes:
        return LoadStaticFiles(
            path=str(os.path.join(StaticFilePath.favicon_path.value, 'favicon.ico'))
        ).load

    @staticmethod
    def CONFIG_DEFAULT() -> dict[str, dict[str, (bool, str, int)]]:
        return toml.loads(LoadStaticFiles(
            path=str(StaticFilePath.config_default.value)
        ).load)

    @staticmethod
    def UPDATE_FILE() -> str:
        return LoadStaticFiles(
            path=str(StaticFilePath.update_file.value)
        ).load
