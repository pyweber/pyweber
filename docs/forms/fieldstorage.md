# FieldStorage

The `FieldStorage` class parses multipart/form-data content from HTTP requests, extracting individual fields and file uploads into Field objects.

## FieldStorage Class

### Constructor
```python
def __init__(self, content_type: str, callbacks: bytes):
```

**Parameters:**
- `content_type`: Content-Type header containing the boundary parameter
- `callbacks`: Raw multipart/form-data content as bytes

### Properties

#### `boundary` (Property with Setter)
Extracts and stores the boundary string from the Content-Type header.

**Getter:** Returns the boundary string used to separate form fields.

**Setter:** Parses the Content-Type header to extract the boundary parameter.
- Raises `TypeError` if no boundary is detected in the content type

#### `callbacks` (Property with Setter)
Stores the raw multipart form data content.

**Getter:** Returns the raw form data as bytes.

**Setter:** Validates and stores the multipart form data.
- Raises `TypeError` if value is not bytes or is empty
- Raises `ValueError` if content doesn't match the expected boundary format

### Methods

#### `fields() -> list[Field]`
Parses the multipart data and returns a list of Field objects.

**Returns:** List of Field objects representing form fields and file uploads

**Processing Logic:**
1. Splits content by boundary delimiters
2. Parses each section for headers and content
3. Extracts field name, filename, and content type using regex
4. Creates Field objects with appropriate data
5. Handles both text fields and file uploads

### Magic Methods

#### `__len__()`
Returns the number of fields in the form data.

```python
field_count = len(fieldstorage_instance)
```

#### `__repr__()`
Returns a string representation showing the number of files/fields.

```python
print(fieldstorage_instance)  # FileStorage(files=3)
```

## Usage Example

```python
from pyweber.models.field_storage import FieldStorage

# Example multipart form data
content_type = "multipart/form-data; boundary=----WebKitFormBoundary7MA4YWxkTrZu0gW"
form_data = b'''------WebKitFormBoundary7MA4YWxkTrZu0gW
Content-Disposition: form-data; name="username"

john_doe
------WebKitFormBoundary7MA4YWxkTrZu0gW
Content-Disposition: form-data; name="avatar"; filename="profile.jpg"
Content-Type: image/jpeg

JPEG binary data here...
------WebKitFormBoundary7MA4YWxkTrZu0gW--
'''

# Create FieldStorage instance
fs = FieldStorage(content_type, form_data)

# Get all fields
fields = fs.fields()

# Access individual fields
for field in fields:
    if field.filename:
        print(f"File: {field.name} = {field.filename} ({field.content_type})")
    else:
        print(f"Field: {field.name} = {field.value.decode()}")

# Get field count
print(f"Total fields: {len(fs)}")
```

## Field Processing

### Text Fields
For regular form fields:
- Extracts `name` from Content-Disposition header
- Sets `filename` to None
- Sets `content_type` to None
- Stores text content as decoded string in `value`

### File Fields
For file uploads:
- Extracts `name` from Content-Disposition header
- Extracts `filename` from Content-Disposition header
- Extracts `content_type` from Content-Type header
- Stores binary file content in `value`

## Error Handling

### Boundary Validation
- `TypeError`: Raised when no boundary parameter is found in content type
- `ValueError`: Raised when form data doesn't match expected boundary format

### Content Validation
- `TypeError`: Raised when callbacks is not bytes or is empty

## Integration

The FieldStorage class is used by:
- `Request` class for parsing multipart form data
- `File` class for creating file objects from parsed fields
- Web frameworks for handling file uploads and form submissions

## Common Use Cases

1. **File Upload Processing**: Parsing uploaded files from HTML forms
2. **Form Data Extraction**: Converting multipart data to structured fields
3. **Content Validation**: Ensuring proper multipart format
4. **Mixed Content Handling**: Processing forms with both text and file fields