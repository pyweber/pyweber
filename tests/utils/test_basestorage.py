import pytest
from pyweber.utils.types import BaseStorage

@pytest.fixture
def base_storage_dict():
    return BaseStorage(data={'name': 'pyweber', 'version': '1.0.0', 'creator': 'Alexandre Zunguze'})

def test_get_dict(base_storage_dict):
    assert base_storage_dict.get('name') == 'pyweber'

def test_keys_dict(base_storage_dict):
    assert base_storage_dict.keys() == ['name', 'version', 'creator']

def test_values_dict(base_storage_dict):
    assert base_storage_dict.values() == ['pyweber', '1.0.0', 'Alexandre Zunguze']

def test_items_dict(base_storage_dict):
    assert base_storage_dict.items()[0] == ('name', 'pyweber')