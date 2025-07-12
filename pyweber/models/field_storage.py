import re
from pyweber.models.field import Field

class FieldStorage: # pragma: no cover
    def __init__(self, content_type: str, callbacks: bytes):
        self.boundary = content_type
        self.callbacks = callbacks
    
    @property
    def boundary(self) -> str: return self.__boundary

    @boundary.setter
    def boundary(self, value: str):
        boundary = re.search(f"boundary=(.+)", value)
        if not boundary:
            raise TypeError('None boundary was detected')
        
        self.__boundary = boundary.group(1)
    
    @property
    def callbacks(self): return self.__callbacks

    @callbacks.setter
    def callbacks(self, value: bytes):
        if not value or not isinstance(value, bytes):
            raise TypeError('callbacks must be bytes instances')
        
        if not value.startswith(f"--{self.boundary}\r\n".encode()) and not value.endswith(f"--{self.boundary}--\r\n".encode()):
            raise ValueError(f'callbacks invalid for boundary {self.boundary}')
        
        self.__callbacks = value
    
    def fields(self) -> list[Field]:
        init_delimiter = f"--{self.boundary}\r\n"
        end_delimiter = f"--{self.boundary}--\r\n"

        values = [
            b.removesuffix("\r\n".encode()) for b in self.callbacks.removeprefix(
                init_delimiter.encode()
            ).removesuffix(
                end_delimiter.encode()
            ).split(init_delimiter.encode())
        ]

        fids: list[Field] = []

        for value in values:
            k, _, v = value.partition("\r\n\r\n".encode())
            keys = k.decode()

            name = re.search(r"name=\"(.+)\"", keys)
            filename = re.search(r"filename=\"(.+)\"", keys)
            content_type = re.search(r"Content-Type: (.+)", keys)
            field = Field()

            if filename:
                field.content_type = content_type.group(1)
                field.name = name.group(1).split('";')[0]
                field.filename = filename.group(1)
                field.value = v

                fids.append(field)
            elif name:
                field.name = name.group(1)
                field.content_type = None
                field.value = v.decode()
                field.filename = None
                fids.append(field)
        
        return fids
    
    def __len__(self):
        return len(self.fields())
    
    def __repr__(self):
        return f'FileStorage(files={self.__len__()})'