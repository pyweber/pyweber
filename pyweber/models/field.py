from dataclasses import dataclass
from typing import Optional

from dataclasses import dataclass
from typing import Optional


class Field: # pragma: no cover
    def __init__(
        self,
        name: Optional[str] = None,
        filename: Optional[str] = None,
        value: Optional[bytes] = b'',
        content_type: Optional[str] = None
    ):
        self.name = name
        self.filename = filename
        self.__value = value
        self.content_type = content_type

    @property
    def value(self): return bytes(self.__value)

    def __repr__(self):
        return f"Field(name={self.name}, value_length={len(self.value)})"