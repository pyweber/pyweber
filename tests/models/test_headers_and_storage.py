import pytest

from pyweber.models.headers import Headers
from pyweber.models.field import Field
from pyweber.models.field_storage import FieldStorage
from pyweber.utils.types import ContentTypes


def test_headers_builds_text_and_json():
    h = Headers(
        url='http://localhost:8800/api',
        method='post',
        content_type=ContentTypes.json,
        content_length=10,
        cookie={'sid': 'abc'},
        user_agent='pytest',
        accept='application/json',
    )
    text = h.text
    assert 'POST' in text
    assert 'localhost:8800' in text
    assert h.json['headers']


def test_headers_setters_validate():
    h = Headers(url='http://localhost/')
    with pytest.raises(ValueError):
        h.http_version = 9.9
    with pytest.raises(TypeError):
        h.cookie = 'bad'
    with pytest.raises(TypeError):
        h.content_type = 'text'
    with pytest.raises(ValueError):
        Headers(url='')


def _multipart_body(boundary: str, name: str, value: str, filename: str = None) -> bytes:
    if filename:
        part = (
            f'--{boundary}\r\n'
            f'Content-Disposition: form-data; name="{name}"; filename="{filename}"\r\n'
            f'Content-Type: text/plain\r\n\r\n'
            f'data\r\n'
        )
    else:
        part = (
            f'--{boundary}\r\n'
            f'Content-Disposition: form-data; name="{name}"\r\n\r\n'
            f'{value}\r\n'
        )
    return (part + f'--{boundary}--\r\n').encode()


def test_field_storage_parses_fields():
    boundary = 'abc123'
    body = _multipart_body(boundary, 'user', 'joao')
    fs = FieldStorage(f'multipart/form-data; boundary={boundary}', body)
    fields = fs.fields()
    assert len(fields) == 1
    assert fields[0].name == 'user'
    assert fields[0].value == 'joao'
    assert len(fs) == 1
    assert 'FileStorage' in repr(fs)


def test_field_storage_file_upload():
    boundary = 'xyz'
    body = _multipart_body(boundary, 'doc', '', filename='a.txt')
    fs = FieldStorage(f'multipart/form-data; boundary={boundary}', body)
    fields = fs.fields()
    assert fields[0].filename == 'a.txt'
    assert fields[0].size == len(fields[0].value)


def test_field_storage_invalid_boundary():
    with pytest.raises(TypeError):
        FieldStorage('invalid', b'')
    fs = FieldStorage('multipart/form-data; boundary=b', b'--b--\r\n')
    with pytest.raises(TypeError):
        fs.callbacks = 'not-bytes'
    with pytest.raises(ValueError):
        fs.callbacks = b'invalid-body'


def test_field_repr():
    f = Field(name='a', value=b'x', size=1)
    assert 'Field' in repr(f)
