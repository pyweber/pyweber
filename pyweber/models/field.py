from dataclasses import dataclass
from typing import Optional

@dataclass
class Field:
    name: Optional[str] = None
    filename: Optional[str] = None
    value: Optional[bytes] = b''
    content_type: Optional[str] = None

    def __repr__(self):
        return f"Field(name={self.name}, value_length={len(self.value)})"