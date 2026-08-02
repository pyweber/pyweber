from pyweber.models.field import Field
from pyweber.utils.security import secure_filename as _secure_filename
from pyweber.utils.mime import validate_upload, sniff_mime


class File:
    def __init__(self, field: Field):
        self.filename = field.filename
        self.content = field.value
        self.size = field.size
        self.content_type = field.content_type
        self.file_id = field.field_id

    @staticmethod
    def secure_filename(filename: str | None) -> str:
        return _secure_filename(filename)

    def sniff_mime(self) -> str | None:
        data = self.content if isinstance(self.content, (bytes, bytearray)) else None
        return sniff_mime(data)

    def validate(self, allowed: list[str] | None = None) -> str:
        data = self.content if isinstance(self.content, (bytes, bytearray)) else b''
        return validate_upload(
            data,
            filename=self.filename,
            declared_type=self.content_type,
            allowed=allowed,
        )

    def __len__(self):
        return self.size

    def __repr__(self):
        return f"File(filename={self.filename}, size={self.size}, type={self.content_type})"
