# File streaming (large uploads)

For large files, Pyweber can request file chunks from the browser over WebSocket while the HTTP server receives the data — without blocking other requests.

## Basic pattern

```python
import asyncio
import pyweber as pw

app = pw.Pyweber()

class UploadForm(pw.Element):
    def __init__(self):
        super().__init__(tag='div', classes=['container'])
        self.childs = [
            pw.InputFile(name='files', accept='*/*', multiple=True),
            pw.InputButton(name='submit', onclick=self.start_upload),
        ]

    async def save_one(self, e: pw.EventHandler, file: pw.File):
        chunks = app.stream(
            file=file,
            session_id=e.session.session_id,
            max_size=1024 * 1024 * 50,  # adaptive chunk ceiling
        )
        content = b''
        async for chunk in chunks:
            content += chunk

        if len(content) != file.size:
            raise ValueError(f'Incomplete upload: {len(content)}/{file.size}')

        with open(f'assets/{file.filename}', 'wb') as f:
            f.write(content)

    async def start_upload(self, e: pw.EventHandler):
        for inp in e.template.querySelectorAll('input'):
            for file in inp.files or []:
                asyncio.create_task(self.save_one(e, file))

@app.route('/')
def upload_page():
    return UploadForm()

if __name__ == '__main__':
    app.run()
```

## `app.stream()` parameters

| Parameter | Description |
|-----------|-------------|
| `file` | `pw.File` instance from an input’s `files` list |
| `session_id` | Tab session — use `e.session.session_id` |
| `max_size` | Upper bound for adaptive chunk size (bytes) |
| `timeout` | Seconds to wait per chunk (default `30`) |

Returns an **async generator** of `bytes` chunks.

## When to use streaming vs direct `files`

| Scenario | Approach |
|----------|----------|
| Small files, immediate read in handler | `inp.files` in memory |
| Large files (MB+) | `app.stream()` |
| Traditional form POST | `FieldStorage` / request body |

## Static directory for saved files

Register where uploads should be served from:

```python
app = pw.Pyweber()
app.static('assets', 'static')
```

Only directories registered via `Pyweber(...)` or `app.static()` are exposed as static files.

## Next steps

- [Components](components.md) — `InputFile` reference
- [Pyweber application](../core/pyweber.md) — `static()` and routing
