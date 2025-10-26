from datetime import datetime
from typing import Literal
from pyweber.utils.types import Colors

def PrintLine(
    text: str,
    with_hour: bool = True,
    with_date: bool = False,
    splitter: str = '-',
    level: Literal['INFO', 'WARNING', 'ERROR'] = 'INFO',
    file_path: str = None
):
    final_value = format_text(text, with_hour, with_date, splitter, level=level)

    if file_path:
        with open(file_path, 'a', encoding='utf-8') as file:
            file.write(f"{final_value}\n")
    else:
        print(final_value)

def WriteLine(text: str = '', with_hour: bool = True, with_date: bool = False, splitter: str = '-'):
    return input(f'{format_text(text, with_hour, with_date, splitter)}')

def format_text(text: str, with_hour: bool = True, with_date: bool = False, splitter: str = '-', level: str =  'INFO'):
    reset = Colors.RESET
    curr_time = current_time(with_hour=with_hour, with_date=with_date, splitter=splitter)

    return f"{color(level=level)}{str(level).upper():<10}{curr_time}{reset}{text}"

def color(level: str):
    if str(level).upper() == 'WARNING':
        return Colors.YELLOW
    elif str(level).upper() == 'ERROR':
        return Colors.RED
    return Colors.BLUE

def current_time(with_hour: bool, with_date: bool, splitter: str):
    if with_date and with_hour:
        return f"{datetime.now().strftime('%d/%m/%Y {spl} %H:%M:%S').format(spl=splitter)}\t"
    
    if with_hour:
        return f"{datetime.now().strftime('[%H:%M:%S]')}\t"
    
    if with_date:
        return f"{datetime.now().strftime('[%d/%m/%Y]')}\t"
    return ''