from pathlib import Path
import toml

from pyweber.utils.loads import StaticTemplates

class PyweberConfig:
    def __init__(self):
        self.__config = self.__defaults.copy()
        self.__extensions_allowed = ['toml']
        self.__path, self.__name, self.__keep_defaults = '.pyweber', 'config.toml', True
        self.__load_from_file()
    
    @property
    def path(self):
        return str(Path(self.__path, self.__name))
    
    @property
    def keys(self):
        return list(self.__config.keys())
    
    @property
    def config(self):
        return self.__config

    @property
    def __defaults(self):
        return StaticTemplates.CONFIG_DEFAULT()
    
    def set_parameters(self, path: str | None = None, name: str | None = None, keep_defaults: bool | None = None):
        """Define the configuration file parameters dynamically, allowing for custom paths and filenames.

        Args:
            path (str, optional): The folder where the config file is located. Defaults to `.pyweber`.
            name (str, optional): The name of the config file. Defaults to `config.toml`.
            keep_defaults (bool, optional): Whether to keep default values if no values exist in the config file. Defaults to `True`.
        """
        if not name:
            name = self.__name
        
        if not path:
            path = self.__path
        
        if keep_defaults is None:
            keep_defaults = self.__keep_defaults
        
        if not any(name.endswith(ext) for ext in self.__extensions_allowed):
            raise ValueError(f'Config file must be a toml file, but you got {str(name).split('.')[-1]} file')

        self.__path, self.__name, self.__keep_defaults = path, name, keep_defaults

        if not Path(path).is_dir():
            Path(path).mkdir(exist_ok=True)
        
        if not Path(path, name).exists():
            with open(str(Path(path, name)), 'w', encoding='utf-8') as file:
                toml.dump(self.__defaults, file)
        
        self.__load_from_file()

    def get(self, *keys, default=None):
        current = self.config
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default
        return current
    
    def set(self, *keys, value):
        current = self.config
        for key in keys[:-1]:
            current = current.setdefault(key, {})
        
        if not value:
            current[keys[-1]] = {}
        else:
            current[keys[-1]] = value

        self.save()
    
    def delete(self, *keys):
        current = self.config
        for key in keys[:-1]:
            current = current.get(key, {})
        current.pop(keys[-1], None)
        self.save()
    
    def save(self):
        with open(self.path, 'w') as file:
            toml.dump(self.config, file)
    
    def show(self):
        import pprint
        pprint.pprint(self.config)
    
    def __load_from_file(self):
        try:
            with open(Path(self.__path, self.__name), 'r', encoding='utf-8') as file:
                file_config = toml.loads(file.read())
                self.__merge_configs(target=self.__config, source=file_config)
        
        except FileNotFoundError:
            pass

        except Exception as e:
            print(f'Error to load the config file: {e}')
    
    def __merge_configs(self, target: dict[str, dict[str, str | int]], source: dict[str, dict[str, str | int]]):
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self.__merge_configs(target=target[key], source=value)

            elif self.__keep_defaults and self.__is_empty_value(value) and key in target:
                pass
            
            else:
                target[key] = value
    
    def __is_empty_value(self, value) -> bool:
        """Check if a value is empty."""
        if value is None:
            return True

        if isinstance(value, str) and value.strip() == "":
            return True

        if isinstance(value, (list, dict, set, tuple)) and len(value) == 0:
            return True

        return False
    
    def __getitem__(self, section: str):
        return self.__config.get(section, {})

config = PyweberConfig()