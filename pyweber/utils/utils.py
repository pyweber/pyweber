from datetime import datetime
from pyweber.utils.types import Colors

def print_line(text: str, with_date: bool = False):
    blue = Colors.BLUE.value
    reset = Colors.RESET.value
    print(f'{blue}{current_time(with_date=with_date)}{reset}\t{text}')

def current_time(with_date: bool):
    if with_date:
        return datetime.now().strftime("%d/%m/%Y - [%H:%M:%S]")
    
    return datetime.now().strftime("[%H:%M:%S]")