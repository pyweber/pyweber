# Element model: `childs`, `content` and placeholders

This is the most important concept in Pyweber templates. Many “weird” ordering bugs come from misunderstanding how **text** and **child elements** work together.

## Two channels, one tree

Every `Element` stores children in two places:

| Channel | What it holds | Role |
|---------|---------------|------|
| `childs` | List of `Element` objects | The logical DOM tree |
| `content` | String, often with `{{uuid}}` markers | **Where** each child appears in the HTML |

When you parse HTML like `<div>Hello <b>world</b></div>`, Pyweber automatically builds both:

- `content` ≈ `"Hello {{uuid-of-b}}"`
- `childs` = `[Element('b', content='world')]`

When you build elements in Python, you must follow the same rules — or order will break.

## Placeholder syntax

Use **double braces** with the child’s UUID:

```python
icon = pw.Element('i', classes=['bi', 'bi-play-fill'])
button = pw.Element('button', childs=[icon])
button.content = f"{{{{{icon.uuid}}}}} Start"  # {{uuid}} Start
```

In HTML template files, use **kwargs placeholders** (also double braces):

```html
<h1>Welcome, {{username}}!</h1>
```

```python
class Page(pw.Template):
    def __init__(self, username: str):
        super().__init__(template="welcome.html", username=username)
```

!!! warning "Common mistake"
    Old docs sometimes showed `{uuid}` with single braces. The correct runtime syntax is always **`{{...}}`**.

## Recommended patterns

### 1. Text before children (most common)

```python
bold = pw.Element('b', content='world')
parent = pw.Element('div', content='Hello ', childs=[bold])
# Renders: <div>Hello <b>world</b></div>
```

When you assign `childs`, Pyweber registers `{{uuid}}` in `content` automatically.

!!! warning "Icon + `{{slot}}` in content — do not duplicate in `childs`"
    If you use a kwargs slot in `content`, e.g. `content='{{icon}} Título'` with `icon=Icon(...)`, **do not** pass the same `Icon` again in `childs` unless you need it for server-side queries. Before 1.3.0 this rendered the icon twice in HTML. Prefer one of:

    ```python
    # Option A — slot in childs (recommended)
    Element('h2', childs=['{{icon}}', Element('span', content='Requerimentos')], icon=Icon('bi-folder'))

    # Option B — slot in content only (no duplicate in childs)
    Element('h2', content='{{icon}} Requerimentos', icon=Icon('bi-folder'))
    ```

### 2. Slot between siblings (`{{slot}}` in child list)

Pass a named element via kwargs and use a placeholder string in `childs`:

```python
left = pw.Element('span', content='Left')
middle = pw.Element('em', content='Middle')
right = pw.Element('span', content='Right')

parent = pw.Element(
    'div',
    childs=[left, '{{middle}}', right],
    middle=middle,
)
# Order: Left → Middle → Right
```

### 3. Adding children after creation

Prefer `add_child()` or `childs.append()` — both sync placeholders:

```python
parent = pw.Element('div', content='Items: ')
parent.add_child(pw.Element('span', content='first'))
parent.add_child(pw.Element('span', content='second'))
```

### 4. Mixing text and elements manually

If you set `content` and `childs` separately without placeholders, children may render **after** all text. Prefer patterns 1–3 instead.

## Parsing HTML vs building in Python

| Source | Order preserved? |
|--------|------------------|
| `Element.from_html(...)` / template files | Yes — parser writes placeholders |
| `childs=[...]` with `content='...'` | Yes — since 1.2.x placeholder sync |
| `childs=[...]` without `content` | Yes — placeholders appended in child order |
| Only `add_child()` after init | Yes — placeholder appended per child |

## Dynamic values in `content`

`{{variable}}` in `content` can refer to:

1. **Constructor kwargs** — replaced when rendering (`username`, `title`, …)
2. **Child UUID** — replaced with rendered child HTML (`{{abc-123-...}}`)

UUID placeholders are registered automatically when you add children. Kwargs placeholders come from your template HTML or Python strings.

## `include_uuid`

When converting elements to HTML for debugging or export:

```python
html = element.to_html(include_uuid=False)  # hide internal UUID attributes
```

## Quick checklist

- [ ] Use `{{double braces}}`, not single `{braces}`
- [ ] After changing `childs`, call `e.update()` in event handlers
- [ ] Prefer `add_child` / `append` over manual string concatenation
- [ ] For layout slots, use `'{{name}}'` in `childs` + kwargs
- [ ] Parse HTML from files when the structure is mostly static

## Next steps

- [Templates](../ui/template.md) — pages and `querySelector`
- [Reactivity & updates](reactivity.md) — `e.update()` and WebSocket diffs
- [Components](components.md) — form inputs and UI building blocks
