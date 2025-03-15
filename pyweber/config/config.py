from pathlib import Path
import secrets
import json

class PyweberConfig:
    def __init__(self, keep_defaults_on_empty: bool = True):
        self.__config = self.__defaults.copy()
        self.__keep_defaults_on_empty = keep_defaults_on_empty
        self.load_from_file()
    
    @property
    def keep_defaults_on_empty(self):
        return self.__keep_defaults_on_empty
    
    @keep_defaults_on_empty.setter
    def keep_defaults_on_empty(self, value: bool):
        if not isinstance(value, bool):
            raise ValueError(f'Incorret value for this attribute, is needed bool, but got {type(value).__name__}')
        
        self.__keep_defaults_on_empty = value

    def get(self, section: str, key: str | None = None, default = None):
        if section not in self.__config:
            return default
        
        if key is None:
            return self.__config[section]
        
        return self.__config[section].get(key, default)
    
    def load_from_file(self):
        try:
            with open(Path('.pyweber', 'config.json'), 'r', encoding='utf-8') as file:
                file_config = json.loads(file.read())
                self.__merge_configs(target=self.__config, source=file_config)
        
        except FileNotFoundError:
            pass

        except Exception as e:
            print(f'Error to load the config file: {e}')
    
    def __merge_configs(self, target: dict[str, dict[str, str | int]], source: dict[str, dict[str, str | int]]):
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self.__merge_configs(target=target[key], source=value)

            elif self.__keep_defaults_on_empty and self.__is_empty_value(value) and key in target:
                pass
            
            else:
                target[key] = value
    
    def __is_empty_value(self, value) -> bool:
        """Verifica se um valor é considerado vazio."""
        if value is None:
            return True

        if isinstance(value, str) and value.strip() == "":
            return True

        if isinstance(value, (list, dict, set, tuple)) and len(value) == 0:
            return True

        return False

    def __getitem__(self, section: str):
        return self.__config.get(section, {})
    
    @property
    def config(self):
        return self.__config

    @property
    def __defaults(self) -> dict[str, dict[str, str | int]]:
        return {
            'app': {
                'name': 'Pyweber App',
                'version': '0.1.0',
                'description': 'A powerfull app made with pyweber framework',
                'icon': str(Path('src', 'assets', 'favicon.ico'))
            },
            'server': {
                'host': '0.0.0.0',
                'port': 8800,
                'route': '/'
            },
            'websocket': {
                'host': 'localhost',
                'port': 8765
            },
            'database': {
                'type': '',
                'name': '',
                'username': '',
                'password': '',
                'host': '',
                'port': '',
                'dsn': '',
                'ssl': ''
            },
            'api_keys': {},
            'session': {
                'secret_key': secrets.token_hex(nbytes=32),
                'timeout': 3600,
                'reload_mode': False,
                'env': 'development'
            },
            'requirements': [

            ]
        }

config = PyweberConfig()