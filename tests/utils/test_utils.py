from datetime import datetime
from pyweber.utils.utils import (
    PrintLine,
    WriteLine
)

def helder_func(capsys, with_hour: bool, with_date: bool, text: str = 'Hello world') -> tuple[datetime, str]:
    now = datetime.now()
    PrintLine(text=text, with_hour=with_hour, with_date=with_date)
    return now, capsys.readouterr().out.strip()

def test_printline(capsys):
    _, out = helder_func(capsys, False, False)
    assert out.endswith("Hello world")

def test_printline_with_hour(capsys):
    now, out = helder_func(capsys, True, False)
    assert now.strftime("%H:%M") in out

def test_printline_with_date(capsys):
    now, out = helder_func(capsys, False, True)
    assert now.strftime("[%d/%m/%Y]") in out

def test_printline_with_date_and_hour(capsys):
    now, out = helder_func(capsys, True, True)
    assert all(v in out for v in [now.strftime("%H:%M"), now.strftime("%d/%m/%Y")])

def test_writeline(monkeypatch):
    monkeypatch.setattr("builtins.input", lambda _: "Hello world")
    result = WriteLine(with_hour=False, with_date=False)
    assert result == "Hello world"