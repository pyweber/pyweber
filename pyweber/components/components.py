from pyweber.core.element import Element
from pyweber.utils.types import Icons
from typing import Union

class Icon(Element):
    def __init__(self, value: Union[Icons, str]):
        super().__init__(tag='i')
        self.classes.append(value.value if isinstance(value, Icons) else value)