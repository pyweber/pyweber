import os
import sys
import toml
from pathlib import Path
from pyweber.utils.types import ContentTypes, StaticFilePath

class LoadStaticFiles:
    
    def __init__(self, path: str):
        self.__script_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
        if sys.platform == 'win32':
            self.__path = path[1:] if path.startswith('/') else path
        else:
            self.__path = path
            self.__path_2 = str(Path(self.__script_dir) / path.removeprefix('/'))
    
    @property
    def load(self) -> str | bytes:
        extension = self.__path.split('.')[-1].strip()
        mode, encoding = 'r', 'utf-8'

        try:
            if ContentTypes.content_list().index(extension) >= ContentTypes.content_list().index('png'):
                mode, encoding='rb', None
        except ValueError:
            pass
        
        if os.path.exists(self.__path):
            return self.__read_file(path=self.__path, mode=mode, encoding=encoding)
        
        try:
            if os.path.exists(self.__path_2):
                return self.__read_file(path=self.__path_2, mode=mode, encoding=encoding)
        except AttributeError:
            pass
        
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