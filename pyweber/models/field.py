from dataclasses import dataclass
from typing import Optional


class Field: # pragma: no cover
    def __init__(
        self,
        name: Optional[str] = None,
        filename: Optional[str] = None,
        value: Optional[bytes] = b'',
        content_type: Optional[str] = None,
        field_id: Optional[str] = None,
        size: Optional[int] = 0
    ):
        self.name = name
        self.filename = filename
        self.value = value
        self.content_type = content_type
        self.field_id = field_id
        self.size = size

    def __repr__(self):
        return f"Field(name={self.name}, value_length={self.size})"