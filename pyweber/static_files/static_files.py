import os
from pyweber.content_type.content_types import ContentTypes

class LoadStaticFiles:
    def __init__(self, path: str):
        self.path = path[1:] if path.startswith('/') else path
    
    @property
    def load(self):
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
        
        raise FileNotFoundError('O aruqivo não existe')