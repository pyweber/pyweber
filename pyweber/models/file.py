from pyweber.models.field import Field

class File:
    def __init__(self, field: Field):
        self.filename = field.filename
        self.content = field.value
        self.size = len(self.content)
        self.content_type = field.content_type
    
    def __len__(self):
        return self.size
    
    def __repr__(self):
        return f"File(filename={self.filename}, size={self.size}, type={self.content_type})"