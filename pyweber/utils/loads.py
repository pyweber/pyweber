import os
import toml
from pyweber.utils.types import ContentTypes, StaticFilePath

class LoadStaticFiles:
    
    def __init__(self, path: str):
        self.path = path[1:] if path.startswith('/') else path
    
    @property
    def load(self) -> str | bytes:
        extension = self.path.split('.')[-1].strip()
        mode = 'r'
        encoding = 'utf-8'

        try:
            byte_index = ContentTypes.content_list().index(extension)
            if byte_index >= ContentTypes.content_list().index('png'):
                mode='rb'
                encoding = None
        
        except:
            pass
        
        if os.path.exists(self.path):
            with open(self.path, mode=mode, encoding=encoding) as file:
                return file.read()
        
        raise FileNotFoundError('File not found, please ensure that path is correct')


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