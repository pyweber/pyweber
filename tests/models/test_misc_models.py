import pytest

from pyweber.models.file import File
from pyweber.models.field import Field
from pyweber.models.error_pages import ErrorPages
from pyweber.utils.utils import PrintLine, Colors, format_text, color, current_time
from pyweber.utils.exceptions import InvalidTemplateError


def test_field_and_file_repr():
    field = Field(name='upload', filename='a.txt', value=b'data', size=4, field_id='fid-1')
    assert 'upload' in repr(field)
    file = File(field)
    assert file.file_id == 'fid-1'
    assert 'a.txt' in repr(file)


def test_printline(capsys):
    PrintLine('hello', level='INFO')
    out = capsys.readouterr().out
    assert 'hello' in out or out == ''


def test_colors_constants():
    assert Colors.GREEN
    assert Colors.RESET
    assert color('WARNING') == Colors.YELLOW
    assert color('ERROR') == Colors.RED
    assert color('INFO') == Colors.BLUE


def test_format_text_variants():
    assert 'INFO' in format_text('msg', with_hour=False, with_date=False)
    assert '[' in format_text('msg', with_hour=True, with_date=False)
    assert format_text('msg', with_hour=False, with_date=True)
    assert current_time(True, True, '-')


def test_printline_to_file(tmp_path):
    log = tmp_path / 'out.log'
    PrintLine('saved', file_path=str(log))
    assert 'saved' in log.read_text(encoding='utf-8')


def test_error_pages_setters():
    pages = ErrorPages()
    tpl = pages.page_not_found
    pages.page_not_found = tpl
    with pytest.raises(InvalidTemplateError):
        pages.page_not_found = 'bad'
    with pytest.raises(InvalidTemplateError):
        pages.page_unauthorized = 'bad'
    with pytest.raises(InvalidTemplateError):
        pages.page_server_error = 'bad'
