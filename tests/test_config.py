from pyweber.config.config import config
from pathlib import Path
import shutil
import pytest


@pytest.fixture(autouse=True)
def reset_config_path():
    original = config.path
    yield
    if original:
        config.set_parameters(path=Path(original).parent, name=Path(original).name)
    else:
        config.set_parameters('.pyweber', 'config.toml')


def test_get_path():
    config.set_parameters('.pyweber', 'config.toml')
    assert config.path == str(Path('.pyweber', 'config.toml'))

def test_get_keys():
    assert config.keys

def test_get_config():
    assert config.config['app']['name'] == 'Pyweber App'

def test_set_parameters():
    config.set_parameters(path='tests/config')

    with pytest.raises(ValueError, match=r'Config file must be a toml file, but you got txt file'):
        raise config.set_parameters(name='config.txt')
    
    shutil.rmtree(Path('tests', 'config'), ignore_errors=True)

def test_get():
    assert config.get('app', 'version') == '0.1.0'

def test_set():
    config.set_parameters('.pyweber', 'config.toml')
    config.set('websocket', 'port', value=8980)
    config.set('database', 'mysql')
    assert config.get('app', 'profile', default='Pyweber App') == 'Pyweber App'

def test_delete():
    config.delete('session', 'timeout')
    assert not config.get('session', 'timeout', default=None)

def test_getitem():
    assert config['server']['port'] == 8800