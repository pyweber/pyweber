from enum import Enum
from pathlib import Path
import secrets
import json

class APP(Enum):
    NAME = ''
    DESCRIPTION = ''
    VERSION = '0.1.0'
    ICON = Path('src', 'assets', 'favicon.ico')

class SERVER(Enum):
    HOST = '0.0.0.0'
    PORT = 8800
    ROUTE = '/'

class DATABASE(Enum):
    TYPE = ''
    NAME = ''
    USERNAME = ''
    PASSWORD = ''
    HOST = ''
    PORT = ''

class SESSION(Enum):
    SECRET_KEY = secrets.token_hex(nbytes=32)
    TIME_OUT = 3600
    RELOAD_MODE = False
    ENVIROMENT = 'development'

class CONFIGFILE:
    @staticmethod
    def read_file(path: str = Path('.pyweber', 'config.json')) -> dict[str, dict[str, str]]:
        try:
            with open(file=path, mode='r', encoding='utf-8') as file:
                return json.load(file)
        
        except:
            return {}