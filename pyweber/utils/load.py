import os
import importlib.util
from pyweber.utils.types import ContentTypes

LIB_ABSOUTE_PATH = importlib.util.find_spec('pyweber').submodule_search_locations[0]

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
            path=os.path.join(LIB_ABSOUTE_PATH, 'static', 'html.py')
        ).load.replace('# ', '')

    @staticmethod
    def BASE_CSS() -> str:
        return LoadStaticFiles(
            path=os.path.join(LIB_ABSOUTE_PATH, 'static', 'css.py')
        ).load.replace('# ', '')
    
    @staticmethod
    def BASE_MAIN() -> str:
        return LoadStaticFiles(
            path=os.path.join(LIB_ABSOUTE_PATH, 'static', 'main.py')
        ).load.replace('# ', '')
    
    @staticmethod
    def JS_STATIC() -> str:
        return LoadStaticFiles(
            path=os.path.join(LIB_ABSOUTE_PATH, 'static', 'js.py')
        ).load.replace('# ', '')
    
    @staticmethod
    def PAGE_NOT_FOUND() -> str:
        return LoadStaticFiles(
            path=os.path.join(LIB_ABSOUTE_PATH, 'static', 'html404.py')
        ).load.replace('# ', '')