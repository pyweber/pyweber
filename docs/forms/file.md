# File

The `File` class represents an uploaded file in HTTP requests, providing a convenient interface for accessing file properties and content.

## File Class

### Constructor
```python
def __init__(self, field: Field):
```

**Parameters:**
- `field`: A Field object containing the file data and metadata

### Properties

#### File Information
- `filename`: Name of the uploaded file
- `content`: File content as bytes
- `size`: Size of the file in bytes (calculated from content length)
- `content_type`: MIME type of the file

### Magic Methods

#### `__len__()`
Returns the size of the file in bytes.

```python
file_size = len(file_instance)  # Returns file.size
```

#### `__repr__()`
Returns a string representation of the File object.

```python
print(file_instance)  # File(filename=document.pdf, size=1024, type=application/pdf)
```

## Usage Example

```python
from pyweber.models.field import Field
from pyweber.models.file import File

# Create a field with file data
field = Field(
    name="upload",
    filename="document.pdf",
    value=b"PDF content here...",
    content_type="application/pdf"
)

# Create a File instance
uploaded_file = File(field)

# Access file properties
print(uploaded_file.filename)      # document.pdf
print(uploaded_file.size)          # Length of content in bytes
print(uploaded_file.content_type)  # application/pdf
print(len(uploaded_file))          # Same as uploaded_file.size

# Access file content
file_data = uploaded_file.content  # bytes object
```

## Integration

The File class is typically used in conjunction with:
- `Field` objects from form data parsing
- `FieldStorage` for handling multipart/form-data
- `Request` class for accessing uploaded files in HTTP requests

## Common Use Cases

1. **File Upload Handling**: Processing files uploaded through HTML forms
2. **File Validation**: Checking file size, type, and name before processing
3. **File Storage**: Saving uploaded files to disk or cloud storage
4. **File Processing**: Reading and manipulating uploaded file content