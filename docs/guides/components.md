# Built-in components

Pyweber ships form and UI components in `pyweber.components`. They extend `Element` with correct attributes, defaults, and behaviour for HTML forms.

## Import

```python
import pyweber as pw

# Short aliases (recommended)
pw.InputText
pw.InputPassword
pw.InputFile
pw.TextArea
pw.Form
pw.Icon
```

## Text inputs

```python
username = pw.InputText(
    name='username',
    id='user-input',
    placeholder='Enter username',
    required=True,
    autocomplete='username',
)

password = pw.InputPassword(
    name='password',
    placeholder='Password',
    showpassword=False,  # toggle visibility button
)
```

## Other input types

```python
email   = pw.InputEmail(name='email', required=True)
number  = pw.InputNumber(name='qty', min=1, max=99)
date    = pw.InputDate(name='birthdate')
file    = pw.InputFile(name='upload', accept='.pdf,.jpg', multiple=True)
checkbox = pw.InputCheckbox(name='terms', value='accept')
radio   = pw.InputRadio(name='plan', value='pro')
```

## TextArea and Form wrapper

```python
notes = pw.TextArea(name='notes', rows=5, placeholder='Comments…')

form = pw.Form(
    action='/submit',
    method='POST',
    childs=[username, password, notes],
)
```

## Icons (Bootstrap Icons)

```python
play = pw.Icon(classes=['bi', 'bi-play-fill'])
```

Include Bootstrap Icons CSS in your template or static assets before using `bi-*` classes.

## File uploads in event handlers

`InputFile` elements expose a `files` list on the element during events — no full form POST required:

```python
async def on_upload(self, e: pw.EventHandler):
    for inp in e.template.querySelectorAll('input'):
        for f in inp.files or []:
            print(f.filename, f.size, f.content_type)
    e.update()
```

For **large files**, use `app.stream()` — see [File streaming](file-streaming.md).

## Custom components

Extend `Element` for reusable UI:

```python
class PrimaryButton(pw.Element):
    def __init__(self, label: str, onclick):
        super().__init__(
            tag='button',
            classes=['btn', 'primary'],
            content=label,
            events=pw.TemplateEvents(onclick=onclick),
        )
```

See [Element model](element-model.md) for mixing text and child elements with placeholders.

## Next steps

- [File streaming](file-streaming.md) — chunked uploads via WebSocket
- [Forms & FieldStorage](../forms/fieldstorage.md) — classic POST form data
