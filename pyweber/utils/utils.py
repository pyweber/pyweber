from datetime import datetime
from pyweber.utils.types import Colors

def PrintLine(text: str, with_hour: bool = True, with_date: bool = False, splitter: str = '-'):
    print(format_text(text, with_hour, with_date, splitter))

def WriteLine(text: str = '', with_hour: bool = True, with_date: bool = False, splitter: str = '-'):
    return input(f'{format_text(text, with_hour, with_date, splitter)}')

def format_text(text: str, with_hour: bool = True, with_date: bool = False, splitter: str = '-'):
    blue, reset = Colors.BLUE, Colors.RESET
    return f'{blue}{current_time(with_hour=with_hour, with_date=with_date, splitter=splitter)}{reset}\t{text}'

def current_time(with_hour: bool, with_date: bool, splitter: str):
    if with_date and with_hour:
        return datetime.now().strftime(f"%d/%m/%Y {splitter} [%H:%M:%S]")
    
    if with_hour:
        return datetime.now().strftime("[%H:%M:%S]")
    
    if with_date:
        return datetime.now().strftime("[%d:%m:%Y]")
    
    return ''